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
async def addmeme(ctx, memeName, url, s, e):
    # Check valid argument entry
    if not memeName.isalnum():
        await ctx.send("memeName not alphanumeric")
        return
    
    if not s or not e:
        await ctx.send("Please enter start and end timestamps.")


    # Convert timestamps to seconds
    try:
        s = convertTime(s)
        e = convertTime(e)

        if (type(s) is str) or (type(e) is str):
            print(s)
            print(e)
            await ctx.send("Conversion went wrong:" + s + e)
            return
            
    except:
        print("Conversion went wrong")
        await ctx.send("Invalid timestamps. Try again")
        return

    # Creating DB and checking if memeName already exists
    db = TinyDB("db.json")
    Meme = Query()
    a = db.search(Meme.name == memeName)
    if a:
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
    stream = stream.audio.filter("atrim", start=s, end=e)
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
    a = db.search(Meme.name == memeName)

    if not a:
        await ctx.send("Meme not in DB. Use '$list' command for all memes or '$addmeme' to register a new meme.")
        return

    # If meme exists, connect to server
    path = a[0]["path"]
    try:
        vc = await connect_vc(ctx.message.author.voice.channel)
    except:
        print("Could not connect or find Voice Client. Try again.")
        pass

    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio(path), after=afterHandler)
    else:
        addToQueue(memeName)


@client.command()
async def remove(ctx, memeName):
    db = TinyDB("db.json")
    Meme = Query()
    a = db.search(Meme.name == memeName)
    if not a:
        await ctx.send("Meme not in DB")
        return
    
    memePath = a[0]["path"]
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
        return a
    
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


def afterHandler(error):
    if error:
        print(error)

    # qdb = TinyDB("queue.json")
    
    # if not qdb.all():
    #     print("Done with queue.")

    # if queue:
    
    print("Handling after playback")


queue = []

def addToQueue(memeName):
    # qdb = TinyDB("queue.json")
    # Queue = Query()
    # a = qdb.search(Queue.name == "memeQueue")

    # if not a:
    #     qdb.insert({"name": "memeQueue", "memeQ": [memeName]})
    
    queue.prepend(memeName)

    print(f"\"{memeName}\" added to queue in position {len(queue)}")        


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