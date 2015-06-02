import asyncio
import logging

import aiozmq

from svc.proto import Proto

logger = logging.getLogger('worker')


class TaskWorker(aiozmq.ZmqProtocol):
    transport = None

    def __init__(self, on_close, processor=None, loop=None):
        self.tasks = {}
        self.on_close = on_close
        self.processor = processor
        self.methods = processor.exposed_methods
        if loop:
            self.loop = loop
        self.queue = asyncio.Queue(loop=loop)

        self.proto_handlers = {
            Proto.KA: self._handle_proto_ka,
            # Proto.ACK   : self._handle_proto_ack,
            Proto.TASK: self._handle_proto_task,
        }
        asyncio.async(self._process())

    def connection_made(self, transport):
        self.transport = transport
        msg = [Proto.READY.encode()]
        for method in self.methods:
            msg.append(method.encode())
        transport.write(msg)

    def connection_lost(self, exc):
        self.on_close.set_result(exc)
        logger.info('connection lost')

    def msg_received(self, msg):

        logger.info('recv:{}'.format(msg))

        command = msg[0].decode()

        if command not in self.proto_handlers:
            # Ignore message with unknown command
            return

        self.proto_handlers[command](msg)

    def _handle_proto_task(self, msg):
        task_id = msg[1].decode()
        method = msg[2].decode()
        param = msg[3].decode()

        if method not in self.methods:
            return

        ack_msg = Proto.ACK.encode(), task_id.encode(), Proto.TASK.encode()
        self.transport.write(ack_msg)

        future = asyncio.Future()
        future.add_done_callback(self._callback_task_done)
        self.tasks[task_id] = future

        # Assuming the dispatcher should take care about queue limit
        self.queue.put_nowait((task_id, method, param))

    def _handle_proto_ka(self, msg):
        response = [Proto.KA.encode()]
        self.transport.write(response)

    def _callback_task_done(self, future):
        task_id, data = future.result()
        response = Proto.DONE.encode(), task_id.encode(), data.encode()
        self.transport.write(response)
        del self.tasks[task_id]

    @asyncio.coroutine
    def _process(self):
        while True:
            task_id, method, param = yield from self.queue.get()
            if not hasattr(self.processor, method):
                raise NotImplementedError('Method not supported')
            process_method = getattr(self.processor, method)

            result = yield from process_method(param)
            self.tasks[task_id].set_result((task_id, result))
