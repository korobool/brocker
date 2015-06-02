import json
import asyncio

from aiohttp import web
import zmq
import aiozmq

from svc.brocker.task_dispatcher import TaskDispatcher, DispatchNoFreeWorkerError, \
    DispatchTimeoutError, DispatchBadRequestError


class Handler():
    task_dispatcher = None

    def __init__(self, task_dispatcher):
        self.task_dispatcher = task_dispatcher

    @asyncio.coroutine
    def shorten(self, request):
        post_data = yield from request.json()
        data = {"post_data": post_data}

        try:
            result = yield from self.task_dispatcher.process('shorten', json.dumps(data))
        except (DispatchNoFreeWorkerError, asyncio.CancelledError):
            return web.web_exceptions.HTTPInternalServerError()
        except DispatchTimeoutError:
            return web.web_exceptions.HTTPRequestTimeout()
        except DispatchBadRequestError:
            return web.web_exceptions.HTTPBadRequest()

        return web.Response(
            body=json.dumps(result).encode('utf-8'),
            content_type='application/json')

    @asyncio.coroutine
    def expand(self, request):

        params = {
            'ua_string': request.headers["USER-AGENT"],
            'short_url': request.match_info['hash']
        }

        try:
            result = yield from self.task_dispatcher.process('expand', json.dumps(params))

        except (DispatchNoFreeWorkerError, asyncio.CancelledError):
            return web.web_exceptions.HTTPInternalServerError()
        except DispatchTimeoutError:
            return web.web_exceptions.HTTPRequestTimeout()
        except DispatchBadRequestError:
            return web.web_exceptions.HTTPBadRequest()
        if result:
            return web.Response(
                body=json.dumps(result).encode('utf-8'),
                content_type='application/json')
        else:
            return web.web_exceptions.HTTPNotFound()  # 404


@asyncio.coroutine
def start_task_dispatcher(loop=None):
    if not loop:
        loop = asyncio.get_event_loop()

    dispatcher_closed = asyncio.Future()
    _, task_dispatcher = yield from aiozmq.create_zmq_connection(
        lambda: TaskDispatcher(dispatcher_closed, loop),
        zmq.ROUTER,
        bind='tcp://{}:{}'.format('0.0.0.0', 7777),
        loop=loop
    )
    # logger.info("Starting mixer zmq connection at {host}:{port}".format(
    #     host='0.0.0.0', port=7777))
    return task_dispatcher, dispatcher_closed


if __name__ == '__main__':

    app = web.Application()
    loop = asyncio.get_event_loop()
    task_dispatcher, dispatcher_closed = loop.run_until_complete(
        start_task_dispatcher(loop=loop)
    )

    handler = Handler(task_dispatcher)

    app = web.Application()
    """
    curl -H "Content-Type: application/json" -X POST -d '{"domain":"pm.me","urls":{"apple":"https://itunes.apple.com/us/app/valutcik/id978512096?mt=8","android":"https://play.google.com/store/apps/details?id=me.valutchik.app"},"appId":"app-id-123","userId":"1234567"}' localhost:8080/shorten
    """
    app.router.add_route('POST', r'/shorten', handler.shorten)
    app.router.add_route('GET', r'/expand/{hash}', handler.expand)

    # loop = asyncio.get_event_loop()
    f = loop.create_server(
        app.make_handler(), '0.0.0.0', 8011)
    srv = loop.run_until_complete(f)
    print('serving on', srv.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
