from bson import ObjectId
from pymongo import MongoClient

from journal.base import BaseDict
from .wrap import Database as _Database
from config import journal as journal_conf, display

db = None
_uri = display(journal_conf['mongo']['uri'])
_db = display(journal_conf['mongo']['db'])
if _uri and _db:
    _client = MongoClient(_uri)
    db = _client[_db]
    db = _Database(db)


class MongoBase(BaseDict):
    def __init__(self, _id=None):
        super().__init__()
        self._id = _id

    def __setattr__(self, key, val):
        if isinstance(val, ObjectId):
            self.__dict__[key] = str(val)
        elif key == '_id' and isinstance(val, dict):
            self.__dict__[key] = val.get('$oid')
        else:
            self.__dict__[key] = val

    @property
    def id(self):
        return self._id
