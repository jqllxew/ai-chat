from bson import json_util
from pymongo.collection import Collection


class JsonCollection:
    def __init__(self, collection):
        self.collection = collection

    def __getattr__(self, name):
        # 拦截 find_one 和 find 方法的调用
        if name in ['find_one', 'find']:
            # 返回封装后的新函数
            return self.wrap(getattr(self.collection, name))
        else:
            return getattr(self.collection, name)

    @staticmethod
    def wrap(func):
        def wrapped(*args, **kwargs):
            _result = func(*args, **kwargs)
            if _result is None:
                return _result
            return json_util.dumps(_result)
        return wrapped


class JsonDatabase:
    def __init__(self, database):
        self.database = database

    def __getattr__(self, name):
        _result = getattr(self.database, name)
        if isinstance(_result, Collection):
            return JsonCollection(_result)
        else:
            return _result
