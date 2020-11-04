import os
import pymongo
from pymongo import MongoClient



mongoToken = os.getenv("MONGO_TOKEN")
cluster = MongoClient(mongoToken, 3000)
db = cluster["Memr"]


def get_all_objects(guild_id):
    collection = db[guild_id]
    allObjects = [post for post in collection.find()]
    return allObjects


def get_one_object(guild_id, objName):
    collection = db[guild_id]
    obj = collection.find_one({"name": objName})
    return obj


def save_object(guild_id, objName, fileName, start, end, youtubeUrl):
    collection = db[guild_id]
    obj = collection.find_one({"name": objName})

    if not obj:
        collection.insert_one({
            "name": objName, 
            "filename": f"{fileName}.ogg",
            "start": start,
            "end": end,
            "youtubeUrl": youtubeUrl
        })
        print(f"Inserted {objName} into collection {guild_id}")
        return True
    else:
        print(f"Object already exists")
        return False
    

def delete_object(guild_id, objID):
    collection = db[guild_id]
    obj = collection.find_one({"_id": objID})

    if not obj:
        print(f"Object id - {objID} does not exist in collection - {guild_id}")
        return False

    collection.find_one_and_delete({"_id": objID})
    return True
