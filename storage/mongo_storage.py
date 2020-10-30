import os
import pymongo
from pymongo import MongoClient

# Instatiate MongoDB client
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


def save_object(guild_id, objName, fileName, start, end):
    collection = db[guild_id]
    obj = collection.find_one({"name": objName})

    if not obj:
        collection.insert_one({
            "name": objName, 
            "path": f"{fileName}.ogg",
            "start": start,
            "end": end
        })
        print(f"Inserted {objName} into collection {guild_id}")
        return True
    else:
        print(f"Object already exists")
        return False
    



# print(get_one_object("361113156883316737", "sakdjfke"))
# print(get_all_objects("12347235390234929345"))