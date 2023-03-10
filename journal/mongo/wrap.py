import json
import traceback
from typing import Any
from bson import json_util, ObjectId, SON
from bson.json_util import JSONOptions, DEFAULT_JSON_OPTIONS
from pymongo.collection import Collection
from logger import logger


class JsonCollection:
    wrap_func = {
        "find_json": "find",
        "find_one_json": "find_one",
    }

    def __init__(self, collection):
        self.collection: Collection = collection

    def __getattr__(self, name):
        _name = self.__class__.wrap_func.get(name)
        return self.wrap(name, getattr(self.collection, _name or name))

    def wrap(self, name, func):
        def wrapped(*args, **kwargs):
            arg = args[0] if len(args) else None
            try:
                if isinstance(arg, dict) and '_id' in arg and isinstance(arg['_id'], str):
                    arg['_id'] = ObjectId(arg['_id'])
                logger.debug(f"[mongodb]{self.collection.name}.{name}{args}")
                res = func(*args, **kwargs)
                if name in self.__class__.wrap_func:
                    return to_json(res)
                return res
            except Exception as e:
                logger.error(f"[mongodb]{self.collection.name}.{name}{args}\nerr: {e}")
                # traceback.print_exc()
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
    return _json_convert(obj, DEFAULT_JSON_OPTIONS)


def _json_convert(obj: Any, json_options: JSONOptions) -> Any:
    if hasattr(obj, "items"):
        return SON(((_k_convert(k), _json_convert(v, json_options)) for k, v in obj.items()))
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
        return list((_json_convert(v, json_options) for v in obj))
    try:
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_options)
    except TypeError:
        return obj


def _k_convert(k: str):
    if k == '_id':
        return 'id'
    return k
