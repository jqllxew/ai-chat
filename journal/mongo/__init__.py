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
