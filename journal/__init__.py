import time
from logger import logger
from .base import BaseDict


def reply_log(func):
    def wrapper(self, query, *args, **kwargs):
        jl = default_journal(**self.__dict__)
        try:
            jl.before(query)
            return func(self, query, *args, **kwargs, _done=lambda reply: jl.after(reply))
        except Exception as e:
            jl.error(e)
            raise e

    return wrapper


class Journal(BaseDict):
    def __init__(self, uid=None, model_id=None, from_type=None, ctx=None,
                 prompt_len=None, **kw):
        super().__init__()
        self.uid = uid
        self.model_id = model_id
        self.from_type = from_type
        self.ctx_len = len(ctx) if isinstance(ctx, list) else None
        self.prompt_len = prompt_len

    def before(self, query):
        logger.info(f"[{self.model_id}]uid:{self.uid},query: {query}")

    def after(self, reply):
        logger.info(f"[{self.model_id}]uid:{self.uid},reply: {reply}")

    def error(self, e):
        logger.warn(f"[{self.model_id}]uid:{self.uid},error: {e}")


class JournalMongoDB(Journal):
    def __init__(self, db, **kw):
        super().__init__(**kw)
        self.db = db
        self.id = None
        self.state = 0
        self.query = None
        self.q_time = None
        self.reply = None
        self.r_time = None
        self.err = None

    def before(self, query):
        super().before(query)
        self.query = query
        self.q_time = int(time.time())
        self.id = self.db.journal.insert_one(self.to_dict('db')).inserted_id

    def after(self, reply):
        self.reply = reply.to_dict() if isinstance(reply, BaseDict) else reply
        self.r_time = int(time.time())
        self.state = 1
        super().after(self.reply)
        self.db.journal.update_one({'_id': self.id}, {'$set': self.to_dict('id', 'db')})

    def error(self, e):
        self.r_time = int(time.time())
        self.state = 2
        self.err = str(e)
        super().error(e)
        self.db.journal.update_one({'_id': self.id}, {'$set': self.to_dict('id', 'db')})


def default_journal(**kw) -> Journal:
    from .mongo import db
    if db:
        return JournalMongoDB(db, **kw)
    return Journal(**kw)
