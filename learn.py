import discord
import os
from pytube import YouTube
import ffmpeg 
from discord.ext import commands
from tinydb import TinyDB, Query


def ytff(url, start, end, memeName):
    # yt = YouTube(url)
    # print(yt.streams)
    # yt.streams.get_audio_only().download(output_path="audiofiles/")
    


    stream = ffmpeg.input("audiofiles/Jefe Y Soul - Copacabana Blues.mp4")
    stream = stream.audio.filter("atrim", start=start, end=end, duration=10)
    stream = ffmpeg.output(stream, "audiofiles/output.ogg")
    ffmpeg.run(stream)



ytff("https://www.youtube.com/watch?v=qU67Q3uJxTY&t=1m30s", 142, 151, "copa")


# db = TinyDB("db.json")
# db.insert({"name": "meme", "path": "filepath"})
# meme = Query()
# a = db.search((meme.name == "memeName") & (meme.path == "filepath"))
# print(a)