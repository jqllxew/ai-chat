from pymongo import MongoClient

from database.chat_db import ChatDB
from database.mongo.aop_serializer import JsonDatabase as __Database
from config import database as db_conf, display

db = None
__uri = display(db_conf['mongo']['uri'])
__db = display(db_conf['mongo']['db'])
if __uri and __db:
    try:
        __client = MongoClient(__uri)
        db = __client[__db]
        db = __Database(db)
    except Exception as e:
        print(f"[mongodb] err  {e}")


class ChatMongo(ChatDB):

    def __init__(self):
        super().__init__()

    async def before(self, uid, query, prompt):
        pass

    async def after(self, uid, res_text):
        pass

    async def error(self, uid, e):
        pass
