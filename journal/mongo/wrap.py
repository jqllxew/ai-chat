import json

from bson import json_util, ObjectId
from pymongo.collection import Collection
from logger import logger


class JsonCollection:
    def __init__(self, collection):
        self.collection = collection

    def __getattr__(self, name):
        return self.wrap(name, getattr(self.collection, name))

    @staticmethod
    def wrap(name, func):
        def wrapped(*args, **kwargs):
            if '_id' in kwargs and isinstance(kwargs['_id'], str):
                kwargs['_id'] = ObjectId(kwargs['_id'])
            logger.debug(f"[mongodb] {name}{args}{kwargs}")
            if name in ['find_one', 'find']:
                try:
                    cursor = func(kwargs)
                    return json.loads(json_util.dumps(cursor))
                except Exception as e:
                    logger.error(f"[mongodb] err: {e}")
            else:
                return func(*args, **kwargs)
        return wrapped


class Database:
    def __init__(self, database):
        self.database = database

    def __getattr__(self, name):
        _result = getattr(self.database, name)
        if isinstance(_result, Collection):
            return JsonCollection(_result)
        else:
            return _result

    def __getitem__(self, key):
        return self.__getattr__(key)
