from pymongo import MongoClient
from config import journal as journal_conf, display
from .wrap import Database as _Database, json_dumps, to_json

db = None
_uri = display(journal_conf['mongo']['uri'])
_db = display(journal_conf['mongo']['db'])
if _uri and _db:
    _client = MongoClient(_uri)
    db = _client[_db]
    db = _Database(db)

__all__ = [
    "db", "json_dumps", "to_json"
]
