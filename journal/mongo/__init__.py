from bson import ObjectId
from pymongo import MongoClient
from config import journal as journal_conf, display
from journal.base import BaseDict
from .wrap import Database as _Database, json_dumps, to_json

db = None
_uri = display(journal_conf['mongo']['uri'])
_db = display(journal_conf['mongo']['db'])
if _uri and _db:
    _client = MongoClient(_uri)
    db = _client[_db]
    db = _Database(db)


class MongoBase(BaseDict):
    def __init__(self, _id=None, id: str = None):
        super().__init__()
        self.id = _id or id  # str id
        self._id = None  # ObjectId _id

    def __setattr__(self, key, val):
        if isinstance(val, ObjectId):
            self.__dict__[key] = str(val)
        elif key == 'id' and isinstance(val, dict):
            self.__dict__[key] = val.get('$oid')
        else:
            self.__dict__[key] = val


__all__ = ["db", "MongoBase", "json_dumps", "to_json"]
