import asyncio
import aiozmq
import uuid
import time
from asyncio import CancelledError, TimeoutError
from collections import defaultdict

from svc.proto import Proto

import logging
logger = logging.getLogger()


class DispatchNoFreeWorkerError(Exception):
    pass


class DispatchTimeoutError(Exception):
    pass


class DispatchBadRequestError(Exception):
    pass


class TaskDispatcher(aiozmq.ZmqProtocol):

    MAX_TASKS       = 10
    ALIVE_TIMEOUT   = 60
    MAX_KA_FAILED   = 3
    WAIT_ACK        = 2
    EXEC_TIMEOUT    = 10
    HEARBEAT_TIMEOUT = 1

    transport = None

    def __init__(self, on_close, loop):
        self.on_close = on_close
        self.loop = loop
        self.workers = {}
        self.tasks = {}
        self.acks = {}
        self.methods = defaultdict(set)
        asyncio.async(self._heartbeating(), loop=loop)

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.on_close.set_result(exc)

    def msg_received(self, msg):

        logger.debug('recv:{}'.format(msg))

        identify = ''.join(map(chr, msg[0]))
        command = msg[1].decode()

        if command == Proto.READY:
            if identify in self.workers:
                self._delete_worker(identify)

            worker = {
                'tasks': [],
                'ka_last': time.time(),
                'ka_failed': 0
            }
            self.workers[identify] = worker

            for line in msg[2:]:
                self.methods[line.decode()].add(identify)
            return

        if identify not in self.workers:
            # Ignoring silently messages with unknown identify
            return

        if command == Proto.KA:
            worker = self.workers[identify]
            worker['ka_last'] = time.time()
            worker['ka_failed'] = 0

        elif command in [Proto.DONE, Proto.ACK]:
            task_id = msg[2].decode()
            if task_id not in self.tasks:
                # Ignoring silently messages with unknown task_id
                return

            if command == Proto.DONE:
                data = msg[3].decode()
                self.tasks[task_id]['result'].set_result(data)

            elif command == Proto.ACK:
                acked_cmd = msg[3].decode()
                if self.acks[(task_id, acked_cmd)]:
                    self.acks[(task_id, acked_cmd)].set_result(True)

    @asyncio.coroutine
    def process(self, method, param):
        try:
            task_id = None
            result = None
            if method not in self.methods:
                raise DispatchBadRequestError() 

            identify, _ = self._take_worker(method)
            task_id = self._gen_taskid()
            task = {
                'worker': identify,
                'result': asyncio.Future(),
            }
            self.tasks[task_id] = task

            self.workers[identify]['tasks'].append(task_id)
            msg = (
                bytes(map(ord, identify)),
                Proto.TASK.encode(),
                task_id.encode(),
                method.encode(),
                param.encode()
            )

            yield from self._write_with_ack(task_id, Proto.TASK, msg)

            result = yield from asyncio.wait_for(task['result'], self.EXEC_TIMEOUT)

            return result

        except (TimeoutError, CancelledError):
            raise DispatchTimeoutError()
        # except NoFreeWorkerError:
        #     raise DispatchNoFreeWorkerError()
        finally:
            if task_id:
                self._delete_task(task_id)

    @asyncio.coroutine
    def _write_with_ack(self, task_id, cmd=None, msg=None):
        try:
            future = asyncio.Future()
            self.acks[(task_id, cmd)] = future
            self.transport.write(msg)
            yield from asyncio.wait_for(future, self.WAIT_ACK)

        except asyncio.TimeoutError:
            self.tasks[task_id]['result'].cancel()

        finally:
            del self.acks[(task_id, cmd)]

    def _gen_taskid(self):
        task_id = str(uuid.uuid4())
        if task_id in self.tasks:
            task_id = str(uuid.uuid4())
        return task_id

    def _take_worker(self, method):
        if len(self.workers) < 1:
            raise DispatchNoFreeWorkerError()

        method_workers = [(k, v) for k, v in self.workers.items() \
                            if k in self.methods[method]]

        workers_sorted = sorted(method_workers,
                                key=lambda w: len(w[1]['tasks']))

        worker = next(iter(workers_sorted))
        if len(worker[1]['tasks']) > self.MAX_TASKS:
            raise NoFreeWorkerError()
        return worker

    def _delete_task(self, task_id):
        future = self.tasks[task_id]['result']
        identify = self.tasks[task_id]['worker']
        self.workers[identify]['tasks'].remove(task_id)
        del self.tasks[task_id]

    def _delete_worker(self, identify):
        for task in self.workers[identify]['tasks']:
            self._delete_task(task)

        del self.workers[identify]

        for method in self.methods:
            if identify in self.methods[method]:
                self.methods[method].remove(identify)

    @asyncio.coroutine
    def _heartbeating(self):
        while True:
            now = time.time()
            delete_list = []

            for identify, worker in self.workers.items():
                if now - worker['ka_last'] > self.ALIVE_TIMEOUT:
                    if worker['ka_failed'] > self.MAX_KA_FAILED:
                        delete_list.append(identify)
                        continue
                    else:
                        worker['ka_failed'] += 1
                msg = bytes(map(ord, identify)), Proto.KA.encode()
                self.transport.write(msg)

            for worker_id in delete_list:
                self._delete_worker(worker_id)

            yield from asyncio.sleep(self.HEARBEAT_TIMEOUT)

