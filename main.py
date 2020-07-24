import discord
import os
import ffmpeg 
import time
import uuid
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
async def addmeme(ctx, memeName, url, s=0.0, d=10.0):
    # Check valid argument entry
    if not memeName.isalnum():
        await ctx.send("memeName not alphanumeric")
        return
    
    if s < 0 or d < 0:
        await ctx.send("Start and Duration not positive")
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
    stream = stream.audio.filter("atrim", start=s, duration=d)
    stream = ffmpeg.output(stream, f"audiofiles/{fileName}.ogg")
    ffmpeg.run(stream)
    print("Audio trimmed and converted")

    db.insert({"name": memeName, "path": f"audiofiles/{fileName}.ogg"})
    await ctx.send("Meme added to DB. Ready for use.")


@client.command()
async def meme(ctx, memeName):
    db = TinyDB("db.json")
    Meme = Query()
    a = db.search(Meme.name == memeName)
    if not a:
        await ctx.send("Meme not in DB. Use '$list' command for all memes or '$addmeme' to register a new meme.")
        return

    path = a[0]["path"]

    vc = await connect_vc(ctx.message.author.voice.channel)
    
    # stream = ffmpeg.input("pipe:")
    # stream = ffmpeg.output(stream, "output.ogg")
    # ffmpeg.run(stream, capture_stdout=True)

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
    
    db.remove(Meme.name == memeName)
    
    await ctx.send(f"Removed {memeName} from DB.")



def afterHandler(error):
    if error:
        print(error)
    print("Handling after playback")

def addToQueue(memeName):
    print(f"\"{memeName}\" added to queue.")        


async def connect_vc(channel): 
    # Connects to Voice Client if not already connected and returns it.
    vc_list = client.voice_clients
    
    try:
        if not vc_list:
            vc = await channel.connect(timeout=30.0, reconnect=True)
            if vc.is_connected():
                print(f"Successfully connected to Voice Client {vc}")
        else:
            vc = vc_list[0]
            if vc.is_connected():
                print(f"Already connected to Voice Client {vc}")
        return vc

    except:
        print("Could not connect or find Voice Client. Try again.")


client.run(token)