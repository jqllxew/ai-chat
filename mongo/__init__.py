from pymongo import MongoClient
from .aop_serializer import Database as __database


__client = MongoClient('mongodb://admin:jqllxew2014@127.0.0.1:27018/')

db = __client['test']
db = __database(db)

# add test doc
# __collection = db.chat
# doc = {'msg': 'hello ai'}
# result = __collection.insert_one(doc)
# print(result.inserted_id)
