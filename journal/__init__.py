import time
from abc import ABC
from journal.mongo import MongoBase, JlMgData
from logger import logger

table_name = "journal"


class Journal(ABC):
    def __init__(self, uid, model_id, from_type, ctx=None, prompt_len=0,
                 _before=..., _after=..., _error=..., **kwargs):
        self.uid = uid
        self.model_id = model_id
        self.from_type = from_type
        self.ctx_len = len(ctx) if isinstance(ctx, list) else 0
        self.prompt_len = prompt_len
        self._before = _before
        self._after = _after
        self._error = _error

    def before(self, query, prompt):
        if callable(self._before):
            logger.info(self._before(query, prompt))
        else:
            logger.info(f"uid:{self.uid},query: {query}")

    def after(self, reply, data=None):
        if callable(self._after):
            logger.info(self._after(reply, data))
        else:
            logger.info(f"uid:{self.uid},reply: {reply}")

    def error(self, e, data=None):
        if callable(self._error):
            msg = self._error(e, data)
        else:
            msg = f"uid:{self.uid},error: {e}"
        logger.warn(msg)
        return msg


class JournalMongo(Journal):
    def __init__(self, db, collection, **kwargs):
        super().__init__(**kwargs)
        self.c = db[collection]
        self.data = JlMgData(**self.__dict__)

    def before(self, query, prompt):
        super().before(query, prompt)
        self.data.query = query
        self.data.prompt = prompt
        self.data.q_time = int(time.time())
        self.data._id = self.c.insert_one(self.data.to_dict()).inserted_id

    def after(self, reply, data=...):
        self.data.reply = reply
        self.data.r_time = int(time.time())
        self.data.state = 1
        super().after(reply, self.data)
        self.c.update_one({'_id': self.data.id}, {'$set': self.data.to_dict('_id')})

    def error(self, e, data=...):
        self.data.r_time = int(time.time())
        self.data.state = 2
        msg = super().error(e, self.data)
        self.data.error = msg
        self.c.update_one({'_id': self.data.id}, {'$set': self.data.to_dict('_id')})
        return msg


def lifecycle(model_id, **kwargs) -> Journal:
    kwargs['model_id'] = model_id
    from .mongo import db
    if db is not None:
        return JournalMongo(db=db, collection=table_name, **kwargs)
    else:
        return Journal(**kwargs)
