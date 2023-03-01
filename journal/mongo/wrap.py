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
            arg = args[0] if len(args) else None
            try:
                if isinstance(arg, dict) and '_id' in arg and isinstance(arg['_id'], str):
                    arg['_id'] = ObjectId(arg['_id'])
                logger.debug(f"[mongodb] {name}{args}")
                res = func(*args, **kwargs)
                if name in ['find', 'find_one']:
                    return json.loads(json_util.dumps(res))
                return res
            except Exception as e:
                logger.error(f"[mongodb] err: {e}")
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
