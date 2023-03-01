import time

from abc import ABC
from collections import deque
from bson import ObjectId
from logger import logger


class Journal(ABC):
    def __init__(self, uid, model_id, from_type, ctx=None,
                 _before=None, _after=None, _error=None, **kwargs):
        self.uid = uid
        self.model_id = model_id
        self.from_type = from_type
        self.ctx_len = len(ctx) if isinstance(ctx, deque) else 0
        self.ctx_word_len = len("\r\n".join(ctx)) if isinstance(ctx, deque) else 0
        self._before = _before
        self._after = _after
        self._error = _error

    def before(self, query, prompt):
        if callable(self._before):
            logger.info(self._before(query, prompt))
        else:
            logger.info(f"uid:{self.uid},query: {query}")

    def after(self, reply):
        if callable(self._after):
            logger.info(self._after(reply))
        else:
            logger.info(f"uid:{self.uid},reply: {reply}")

    def error(self, e):
        if callable(self._error):
            msg = self._error(e)
        else:
            msg = f"uid:{self.uid},error: {e}"
        logger.warn(msg)
        return msg


class MongoBase:
    def __init__(self, _id, **kw):
        self._id = _id

    def __setattr__(self, key, val):
        if isinstance(val, ObjectId):
            self.__dict__[key] = str(val)
        elif key == '_id' and isinstance(val, dict):
            self.__dict__[key] = val.get('$oid')
        else:
            self.__dict__[key] = val

    def todict(self):
        return dict([(k, v) for k, v in self.__dict__.items() if v is not None])


class JournalMongo(Journal):
    def __init__(self, db, collection, **kwargs):
        super().__init__(**kwargs)
        self.c = db[collection]
        self.db_data = dict(
            uid=self.uid,
            model_id=self.model_id,
            from_type=self.from_type,
            ctx_len=self.ctx_len,
            ctx_word_len=self.ctx_word_len,
            state=0
        )

    def before(self, query, prompt):
        super().before(query, prompt)
        self.db_data['query'] = query
        self.db_data['prompt'] = prompt
        self.db_data['q_time'] = int(time.time())
        self.db_data['_id'] = self.c.insert_one(self.db_data).inserted_id

    def after(self, reply):
        super().after(reply)
        self.db_data['reply'] = reply
        self.db_data['r_time'] = int(time.time())
        self.db_data['state'] = 1
        self.c.update_one({'_id': self.db_data['_id']}, {'$set': self.db_data})

    def error(self, e):
        msg = super().error(e)
        self.db_data['error'] = msg
        self.db_data['r_time'] = int(time.time())
        self.db_data['state'] = 2
        self.c.update_one({'_id': self.db_data['_id']}, {'$set': self.db_data})
        return msg


def lifecycle(model_id, **kwargs)-> Journal:
    kwargs['model_id'] = model_id
    from .mongo import db
    if db is not None:
        return JournalMongo(db=db, collection="journal", **kwargs)
    else:
        return Journal(**kwargs)
