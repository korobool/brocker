from datetime import datetime
import asyncio
import json

from user_agents import parse
from hashids import Hashids
from aiopg.sa import create_engine
import sqlalchemy as sa

from svc.worker.base_processor import BaseProcessor
from utils.dbconstructor import test


class Processor(BaseProcessor):
    def __init__(self, loop=None):
        super(Processor, self).__init__(loop)
        loop.run_until_complete(self._get_pg())

    @asyncio.coroutine
    def _get_pg(self):
        database = "test"

        self.pg_pool = yield from create_engine(
            database=database,
            user="test",
            password="testpasswd",
            host="localhost",
            loop=self.loop
        )

    @asyncio.coroutine
    def _get_ids(self):
        now = datetime.utcnow()
        hashids = Hashids(salt='phone master')
        id = now.strftime("%Y%m%d%H%M%S%f")
        short_hash = hashids.encode(int(id))
        res = {
            "hash": short_hash,
            "id": id
        }
        return res

    @asyncio.coroutine
    def shorten(self, data):
        ids_data = yield from self._get_ids()

        with (yield from self.pg_pool) as conn:
            tr = yield from conn.begin()
            data = json.loads(data)
            data = data["post_data"]
            yield from conn.execute(
                test.insert().values(
                    id=ids_data["id"],
                    short_url=ids_data["hash"],
                    domain=data.get("domain", ""),
                    appId=data.get("appId", ""),
                    userId=data.get("userId", ""),
                    url_android=data.get("urls", {}).get("android", ""),
                    url_apple=data.get("urls", {}).get("apple", "")
                )
            )
            yield from tr.commit()
        resp = {
            "shortUrl": "http://pm.me/{}".format(ids_data["hash"]),
            "hash": ids_data["hash"],
            "id": ids_data["id"]
        }
        return json.dumps(resp)

    @asyncio.coroutine
    def expand(self, data):
        params = json.loads(data)
        short_url = params['short_url']
        user_agent = parse(params['ua_string'])
        device_os = user_agent.os.family

        resp = None
        resp_res = None
        with (yield from self.pg_pool) as conn:
            query = (sa.select([test], use_labels=True)
                .where(test.c.short_url == short_url))
            res = yield from conn.execute(query)
            resp_res = yield from res.fetchone()
        if resp_res:
            resp = {
                "id": resp_res[0],
                "hash": resp_res[1],
                "userId": resp_res[2],
                "appId": resp_res[3],
                "domain": resp_res[4],
                "urls": {
                    "android": resp_res[5],
                    "apple": resp_res[6]
                }
            }
        else:
            resp = {}

        print('!!!!!!!!!!! CONNECTION: {} !!!!!!!!!!'.format(device_os))

        return json.dumps(resp)
