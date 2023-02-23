from pymongo import MongoClient
from mongo.aop_serializer import Database as __Database


__client = MongoClient('mongodb://admin:jqllxew2014@127.0.0.1:27017/')

db = __client['aichat']
db = __Database(db)

# add test doc
# __collection = db.chat
# doc = {'msg': 'hello ai'}
# result = __collection.insert_one(doc)
# print(result.inserted_id)

if __name__ == "__main__":
    u = {"openid": "ssssdssdsaa"}
    _u = db.u_wx.find_one(u)
    print(_u)
    print(type(_u))
    if _u is None:
        print(db.u_wx.insert_one(u).inserted_id)


