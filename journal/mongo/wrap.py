import json
from typing import Any
from bson import json_util, ObjectId, SON
from bson.json_util import JSONOptions, DEFAULT_JSON_OPTIONS
from pymongo.collection import Collection
from logger import logger


class JsonCollection:
    def __init__(self, collection):
        self.collection: Collection = collection

    def __getattr__(self, name):
        if name == 'find_json':
            _name = 'find'
        elif name == 'find_one_json':
            _name = 'find_one'
        else:
            _name = name
        return self.wrap(name, getattr(self.collection, _name))

    def wrap(self, name, func):
        def wrapped(*args, **kwargs):
            arg = args[0] if len(args) else None
            try:
                if isinstance(arg, dict) and '_id' in arg and isinstance(arg['_id'], str):
                    arg['_id'] = ObjectId(arg['_id'])
                logger.debug(f"[mongodb]{self.collection.name}.{name}{args}")
                res = func(*args, **kwargs)
                if name in ['find_json', 'find_one_json']:
                    return to_json(res)
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


def json_dumps(obj, json_options: JSONOptions = DEFAULT_JSON_OPTIONS):
    return json.dumps(_json_convert(obj, json_options))


def to_json(obj):
    return json.loads(json_dumps(obj))


def _json_convert(obj: Any, json_options: JSONOptions) -> Any:
    if hasattr(obj, "items"):
        return SON(((k, _json_convert(v, json_options)) for k, v in obj.items()))
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
        return list((_json_convert(v, json_options) for v in obj))
    try:
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_options)
    except TypeError:
        return obj
