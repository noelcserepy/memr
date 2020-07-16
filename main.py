import discord
import os
import ffmpeg 
from pytube import YouTube
from discord.ext import commands


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
async def meme(ctx, arg):
    vc = await connect_vc(ctx.message.author.voice.channel)

    
    
    stream = ffmpeg.input("pipe:")
    stream = ffmpeg.output(stream, "output.ogg")
    ffmpeg.run(stream, capture_stdout=True)

    

    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio('audiofiles/pusstime.ogg'), after=afterHandler)
    else:
        addToQueue(arg)
        

def afterHandler(error):
    if error:
        print(error)
    print("Handling after playback")

def addToQueue(arg):
    print(f"\"{arg}\" added to queue.")        


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

    

    


out, _ = (ffmpeg
    .input(in_filename, **input_kwargs)
    .output('-', format='s16le', acodec='pcm_s16le', ac=1, ar='16k')
    .overwrite_output()
    .run(capture_stdout=True)
)

client.run(token)