import argparse
import asyncio
import logging
import logging.handlers
import os
import sys
from os.path import join, normpath, abspath, dirname

import aiozmq
import trafaret as t
import yaml
import zmq

from svc.worker.processor import Processor
from svc.worker.task_worker import TaskWorker

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

@asyncio.coroutine
def start_workers(args, proc=None, loop=None):
    workers = {}
    if not loop:
        loop = asyncio.get_event_loop()

    for _ in range(args['connections']):
        worker_closed = asyncio.Future()

        _, worker = yield from aiozmq.create_zmq_connection(
            lambda: TaskWorker(worker_closed, processor=proc, loop=loop),
            zmq.DEALER,
            connect='tcp://{}:{}'.format(args['server'], args['port']),
            loop=loop)

        logger.info("Starting shorter zmq connection at {host}:{port}".format(
            host=args['server'], port=args['port']))

        workers[worker] = worker_closed

    done, pending = yield from asyncio.wait(workers.values())


def get_config_file(config_file_name):
    abs_path = abspath(dirname(__file__))
    full_name = normpath(join(abs_path, config_file_name))
    return open(full_name)


def apply_trafaret(raw_config):
    tr = t.Dict({
        t.Key(
            'logfile_path',
            default=join(dirname(__file__), "logs/shorter.log")
        ) >> 'logfile_path': t.String,
        t.Key('server', default='127.0.0.1') >> 'server': t.String,
        t.Key('port', default=7777) >> 'port': t.Int,
        t.Key('connections', default=1) >> 'connections': t.Int
    })
    return tr.check(raw_config)


if __name__ == '__main__':
     # basic logger
    logging_formatter = logging.Formatter(
        fmt="%(name)s | %(asctime)s | %(levelname)s | %(message)s"
    )
    LOG_FILE_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'logs/shorter.log')
    logging_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=10000000, backupCount=3
    )
    logging_handler.setFormatter(logging_formatter)
    logging_handler.setLevel(logging.INFO)
    logger.addHandler(logging_handler)
    # errors logger
    LOG_ERROR_FILE_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'logs/errors_shorter.log')
    logging_error_handler = logging.handlers.RotatingFileHandler(
        LOG_ERROR_FILE_PATH, maxBytes=10000000, backupCount=3
    )
    logging_error_handler.setLevel(logging.ERROR)
    logging_error_handler.setFormatter(logging_formatter)
    logger.addHandler(logging_error_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--logfile_path', type=str, help='path to log file')
    parser.add_argument(
        '--server', type=str, help='server address')
    parser.add_argument(
        '--port', type=str, help='server port')
    parser.add_argument(
        '--connections', type=int, help='number of connections')
    args = vars(parser.parse_args())

    settings = None

    config_file_name = 'config/shorter.yaml'
    if config_file_name:
        try:
            with get_config_file(config_file_name) as f:
                raw_config = yaml.load(f.read())
                settings = apply_trafaret(raw_config)

        except FileNotFoundError:
            logger.error("Error in shorter: couldn't find config file.")
        except t.DataError as e:
            logger.error("Wrong config file: {}".format(repr(e)))
        except Exception as e:
            logger.error("Error in shorter.", exc_info=True)
            sys.exit(1)
    else:
        logger.error(
            "'config_file_name' is absent \
            'args' should be specified explicitly. Exiting."
        )
        sys.exit(1)

    # Merging settings to args
    if settings:
        args.update({k:v for k,v in settings.items() if not args.get(k)})

    loop = asyncio.get_event_loop()
    try:
        p = Processor(loop=loop)

        tasks = [asyncio.async(start_workers(args, proc=p, loop=loop))]

        loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt:
        logger.warning('Shorter was interrupt!')
