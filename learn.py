import discord
import os
from pytube import YouTube
import ffmpeg 
import time
import uuid
from discord.ext import commands
from tinydb import TinyDB, Query


def ytff(memeName, url, s=0, d=10):
    # Check valid argument entry
    if not memeName.isalnum():
        print("memeName not alphanumeric")
        return
    
    if s < 0 or d < 0:
        print("Start and Duration not positive")
        return

    # Creating DB and checking if memeName already exists
    db = TinyDB("db.json")
    Meme = Query()
    a = db.search(Meme.name == memeName)
    if a:
        print("memeName already exists")
        return

    # Create filename with unique ID
    memeID = uuid.uuid1().hex
    fileName = memeID + " - " + memeName

    # If memeName is new and arguments are valid, the audio is downloaded, trimmed and saved. 
    # memeName and filename are stored in DB.
    yt = YouTube(url)
    saved = yt.streams.get_audio_only().download(output_path="audiofiles/", filename=fileName)
    
    while not saved:
        time.sleep(1)

    print("Audio downloaded")

    stream = ffmpeg.input(f"audiofiles/{fileName}.mp4")
    stream = stream.audio.filter("atrim", start=s, duration=d)
    stream = ffmpeg.output(stream, f"audiofiles/{fileName}.ogg")
    ffmpeg.run(stream)
    print("Audio trimmed and converted")

    db.insert({"name": memeName, "path": f"audiofiles/{fileName}.ogg"})
    print("Meme added to DB")
    

# ytff("oke", "https://www.youtube.com/watch?v=BW1aX0IbZOE", s=5.5)


db = TinyDB("db.json")
Meme = Query()
a = db.search(Meme.name == "oke")
path = a[0]["path"]
print(path)