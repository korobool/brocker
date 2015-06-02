from datetime import datetime
import asyncio
import json

from hashids import Hashids

from aiopg.sa import create_engine
import sqlalchemy as sa

from svc.base_processor import BaseProcessor


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
        id = int(now.strftime("%Y%m%d%H%M%S%f"))
        short_hash = hashids.encode(id)
        res = {
            "hash": short_hash,
            "id": id
            }
        return res

    @asyncio.coroutine
    def shorten(self, data):
        ids_data = yield from self._get_ids()
        resp = {
            "shortUrl": "http://pm.me/{}".format(ids_data["hash"]),
            "hash": ids_data["hash"],
            "id": ids_data["id"]
        }
        return json.dumps(resp)
 
    @asyncio.coroutine
    def expand(self, data):
       resp = {
            "id": "1538542342144",
            "hash": "z1lN3aVAa",
            "userId": "12345",
            "appId": "12345",
            "domain": "pm.me",
            "urls": {
                "android": "https://play.google.com/store/apps/details?id=me.valutchik.app",
                "apple": "https://itunes.apple.com/us/app/valutcik/id978512096?mt=8"
            }
        }
       return json.dumps(resp)
 