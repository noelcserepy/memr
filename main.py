import discord
import os
import ffmpeg 
import time
import uuid
import re
import time
from datetime import datetime
from pytube import YouTube
from discord.ext import commands
from tinydb import TinyDB, Query
import pymongo
from pymongo import MongoClient

# Establishing a connection to the DB
mongoToken = os.getenv("MONGO_TOKEN")
cluster = MongoClient(mongoToken)
db = cluster["Memr"]

# Establishing a connection to the Discord API
discordToken = os.getenv("DISCORD_BOT_TOKEN")
client = commands.Bot(command_prefix='$')


@client.event
async def on_ready():
    print(f"Logged in as {client}")


# Bot joins current voice channel
@client.command()
async def join(ctx):
    senderVoiceChannel = ctx.message.author.voice.channel
    await senderVoiceChannel.connect(timeout=30.0, reconnect=True)


# Bot leaves current voice channel
@client.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()


# Bot echoes any argument
@client.command()
async def test(ctx, arg):
    await ctx.send(arg)


# Bot returns a list of all added memes
@client.command()
async def allmemes(ctx):
    collection = db[str(ctx.guild)]

    if collection.count_documents({}) < 1:
        await ctx.send("You have not yet added any memes. You can add memes by using the $addmeme command")
        return

    allMemes = "Here are the memes you've added so far: \n\n"

    for post in collection.find():
        allMemes += f"${post.get('name')}\n"

    await ctx.send(allMemes)


# Downloads, trims and converts audio file from youtube video and registers name-file relationship in DB. Todo: S3 integration
@client.command()
async def addmeme(ctx, memeName, url, start, end):
    # Check valid argument entry
    if not memeName.isalnum():
        await ctx.send("memeName not alphanumeric")
        return
    
    if not start or not end:
        await ctx.send("Please enter start and end timestamps.")
        return

    # Convert timestamps to seconds
    try:
        start = convertTime(start)
        end = convertTime(end)

        if (type(start) is str) or (type(end) is str):
            print(start)
            print(end)
            await ctx.send("Timecode conversion went wrong")
            return
        if start > end:
            await ctx.send("End timestamp needs to be after starting timestamp. Try again.")
            return
            
    except:
        print("Conversion went wrong")
        await ctx.send("Invalid timestamps. Try again")
        return

    # Creating DB and checking if memeName already exists
    collection = db[str(ctx.guild)]
    if collection.find_one({"name": memeName}):
        await ctx.send("Meme name already exists. Try again.")
        return

    # Create filename with unique ID
    memeID = uuid.uuid1().hex
    fileName = memeID + " - " + memeName

    # Audio is downloaded, trimmed and saved. Meme is saved in DB
    yt = YouTube(url)
    saved = yt.streams.get_audio_only().download(output_path="audiofiles/", filename=fileName)
    
    sleptFor = 0
    while not saved:
        time.sleep(1)
        sleptFor += 1
        if sleptFor > 20:
            ctx.send("Video download time expired.")

    print("Audio downloaded")

    stream = ffmpeg.input(f"audiofiles/{fileName}.mp4")
    stream = stream.audio.filter("atrim", start=start, end=end)
    stream = ffmpeg.output(stream, f"audiofiles/{fileName}.ogg")
    ffmpeg.run(stream)
    print("Audio trimmed and converted")

    collection.insert_one({"name": memeName, "path": f"audiofiles/{fileName}.ogg"})

    mp4Exists = os.path.exists(f"audiofiles/{fileName}.mp4")
    oggExists = os.path.exists(f"audiofiles/{fileName}.ogg")

    # Old mp4 file is removed
    if mp4Exists and oggExists:
        os.remove(f"audiofiles/{fileName}.mp4")
    else:
        print("Could not remove mp4 because it doesn't exist.")

    await ctx.send(f"\"{memeName}\" meme has been added to your collection! Use it with the command $meme {memeName}")


# Recalls meme with chosen name argument. Todo: fetch from S3
@client.command()
async def meme(ctx, memeName):
    # Searching if meme exists
    collection = db[str(ctx.guild)]
    docToPlay = collection.find_one({"name": memeName})
    if not docToPlay:
        await ctx.send("This meme is not in the database. Use \"$allmemes\" command for all memes or \"$addmeme\" to register a new meme.")
        return

    path = docToPlay.get("path")

    # Connect to voice channel
    try:
        vc = await connect_vc(ctx.message.author.voice.channel)
    except:
        await ctx.send("Could not connect or find Voice Client. Try again.")
        return

    # Function for handling errors and queueing next clip
    def afterHandler(error):
        if error:
            print(error)
            ctx.send("An error has ocurred: ", error)
            pass

        qdb = TinyDB("queue.json")
        
        if not qdb.all():
            print("Done with queue.")
            return
        else:
            doc = qdb.all()[0]

            qname = doc["name"]
            qpath = doc["path"]
            docID = doc.doc_id

            qdb.remove(doc_ids=[docID])

            vc.play(discord.FFmpegPCMAudio(qpath), after=afterHandler)


    # Playing audio
    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio(path), after=afterHandler)
    else:
        addToQueue(memeName, path)


# Removes meme audio file and DB entry
@client.command()
async def remove(ctx, memeName):
    db = TinyDB("db.json")
    Meme = Query()
    memeDocList = db.search(Meme.name == memeName)
    if not memeDocList:
        await ctx.send("Meme not in DB")
        return
    
    memePath = memeDocList[0]["path"]
    if os.path.exists(memePath):
        os.remove(memePath)
        print(f"Removed audio file for \"{memeName}\".")

    db.remove(Meme.name == memeName)
    
    await ctx.send(f"Removed \"{memeName}\" from DB.")


# Converts timecode format entered by user to seconds
def convertTime(a):
    if not re.match(r"^[0-9:.]+$", a):
        return "Invalid Timecode"
        
    b = a.split(":")
    
    if len(b) == 1:
        return float(a)
    
    if len(b) == 2:
        if "." in b[0]:
            return "No decimals in the minutes pls"

        if int(b[0]) >= 60:
            return "Can't have more than 60 minutes in an hour, dummy."


        if float(b[1]) >= 60:
            return "Can't have more than 60 seconds in a minute, dummy."

        mins = int(b[0]) * 60
        secs = float(b[1]) 
        return mins + secs
    
    if len(b) == 3:
        if "." in b[0]:
            return "No decimals in the hours pls"
        
        if int(b[0]) > 5:
            return "That's a really long video. I am not bothering to download that."

        if "." in b[1]:
            return "No decimals in the minutes pls"

        if int(b[1]) >= 60:
            return "Can't have more than 60 minutes in an hour, dummy."

        if float(b[2]) >= 60:
            return "Can't have more than 60 seconds in a minute, dummy."
            

        hrs = int(b[0]) * 60 * 60
        mins = int(b[1]) * 60
        secs = float(b[2])
        return hrs + mins + secs


# Callback function to add to-be-played memes to a playback queue
def addToQueue(memeName, path):
    qdb = TinyDB("queue.json")
    qdb.insert({"name": memeName, "path": path})
    print(f"\"{memeName}\" added to queue")        


# Connects bot to a voice channel
async def connect_vc(channel): 
    # Connects to Voice Client if not already connected and returns it.
    vc_list = client.voice_clients
    
    if not vc_list:
        vc = await channel.connect(timeout=30.0, reconnect=True)
        if vc.is_connected():
            print(f"Successfully connected to Voice Client {vc}")
    else:
        vc = vc_list[0]
        if vc.is_connected():
            print(f"Already connected to Voice Client {vc}")
    return vc
    

client.run(discordToken)