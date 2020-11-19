import os
from pymongo import MongoClient
from errors.errors import MongoError



mongoToken = os.getenv("MONGO_TOKEN")
cluster = MongoClient(mongoToken, 3000)
db = cluster["Memr"]


def get_all_objects(guild_id):
    try:
        collection = db[guild_id]
        allObjects = [post for post in collection.find()]
        return allObjects
    except:
        raise MongoError("Failed fetching multiple objects from MongoDB")

def get_one_object(guild_id, objName):
    try:
        collection = db[guild_id]
        obj = collection.find_one({"name": objName})
        return obj
    except:
        raise MongoError("Failed fetching single object from MongoDB.")

def save_object(guild_id, memeData):
    try:
        collection = db[guild_id]
        memeName = memeData.get("name")
        obj = collection.find_one({"name": memeName})

        if not obj:
            collection.insert_one(memeData)
            print(f"Inserted {memeName} into collection {guild_id}")
        else:
            raise MongoError("Object already exists")
    except MongoError:
        raise
    except:
        raise MongoError("Failed storing data to MongoDB.")

def delete_object(guild_id, objID):
    try:
        collection = db[guild_id]
        collection.find_one_and_delete({"_id": objID})
    except:
        raise MongoError("Failed deleting data from MongoDB.")