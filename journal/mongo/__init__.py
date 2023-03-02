from bson import ObjectId
from pymongo import MongoClient

from journal.mongo.wrap import Database as _Database
from config import journal as journal_conf, display

db = None
_uri = display(journal_conf['mongo']['uri'])
_db = display(journal_conf['mongo']['db'])
if _uri and _db:
    _client = MongoClient(_uri)
    db = _client[_db]
    db = _Database(db)


class MongoBase:
    def __init__(self, _id=None):
        self._id = _id

    def __setattr__(self, key, val):
        if isinstance(val, ObjectId):
            self.__dict__[key] = str(val)
        elif key == '_id' and isinstance(val, dict):
            self.__dict__[key] = val.get('$oid')
        else:
            self.__dict__[key] = val

    def to_dict(self, *ks, include=False):
        def judge(k, v):
            if v is None:
                return False
            if include:
                return k in ks
            return k not in ks
        return {k: v for k, v in self.__dict__.items() if judge(k, v)}

    @property
    def id(self):
        return self._id


class JlMgData(MongoBase):
    def __init__(self, _id=None, uid=None, model_id=None, from_type=None,
                 ctx_len=0, prompt_len=0, state=0, **kw):
        super().__init__(_id)
        self.uid = uid
        self.model_id = model_id
        self.from_type = from_type
        self.ctx_len = ctx_len
        self.prompt_len = prompt_len
        self.state = state
        self.query = None
        self.prompt = None
        self.q_time = None
        self.reply = None
        self.r_time = None
        self.error = None
        self.other = None
