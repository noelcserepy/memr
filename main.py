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


token = os.getenv("DISCORD_BOT_TOKEN")
client = commands.Bot(command_prefix='$')


@client.event
async def on_ready():
    print(f"Logged in as {client}")


@client.command()
async def join(ctx):
    senderVoiceChannel = ctx.message.author.voice.channel
    await senderVoiceChannel.connect(timeout=30.0, reconnect=True)


@client.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()


@client.command()
async def test(ctx, arg):
    await ctx.send(arg)


@client.command()
async def addmeme(ctx, memeName, url, start, end):
    # Check valid argument entry
    if not memeName.isalnum():
        await ctx.send("memeName not alphanumeric")
        return
    
    if not start or not end:
        await ctx.send("Please enter start and end timestamps.")


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
            
    except:
        print("Conversion went wrong")
        await ctx.send("Invalid timestamps. Try again")
        return

    # Creating DB and checking if memeName already exists
    db = TinyDB("db.json")
    Meme = Query()
    memeDocList = db.search(Meme.name == memeName)
    if memeDocList:
        await ctx.send("memeName already exists")
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
    stream = stream.audio.filter("atrim", start=start, end=end)
    stream = ffmpeg.output(stream, f"audiofiles/{fileName}.ogg")
    ffmpeg.run(stream)
    print("Audio trimmed and converted")

    db.insert({"name": memeName, "path": f"audiofiles/{fileName}.ogg"})

    mp4Exists = os.path.exists(f"audiofiles/{fileName}.mp4")
    oggExists = os.path.exists(f"audiofiles/{fileName}.ogg")

    if mp4Exists and oggExists:
        os.remove(f"audiofiles/{fileName}.mp4")
    else:
        print("Could not remove mp4 because it doesn't exist.")

    await ctx.send("Meme added to DB. Ready for use.")


@client.command()
async def meme(ctx, memeName):
    # Searching if meme already exists
    db = TinyDB("db.json")
    Meme = Query()
    memeDocList = db.search(Meme.name == memeName)

    if not memeDocList:
        await ctx.send("Meme not in DB. Use '$list' command for all memes or '$addmeme' to register a new meme.")
        return

    # If meme exists, connect to server
    path = memeDocList[0]["path"]
    try:
        vc = await connect_vc(ctx.message.author.voice.channel)
    except:
        print("Could not connect or find Voice Client. Try again.")
        pass

    # Function for handling errors and queueing next clip
    def afterHandler(error):
        if error:
            print(error)
            ctx.send("An error has ocurred: ", error)
            pass

        qdb = TinyDB("queue.json")
        
        if not qdb.all():
            print("Done with queue.")
        else:
            doc = qdb.all()[0]

            qname = doc["name"]
            qpath = doc["path"]
            docID = doc.doc_id

            qdb.remove(doc_ids=[docID])

            vc.play(discord.FFmpegPCMAudio(qpath), after=afterHandler)

            

    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio(path), after=afterHandler)
    else:
        addToQueue(memeName, path)


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



def addToQueue(memeName, path):
    qdb = TinyDB("queue.json")
    qdb.insert({"name": memeName, "path": path})
    print(f"\"{memeName}\" added to queue")        


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


client.run(token)