import discord
from discord.ext import commands

import os
import uuid
import re
import time
import tempfile
import shutil

from util import queue, temp_ctx_manager
from storage import GCS, mongo_storage
from meme import meme
from errors import errors



discordToken = os.getenv("DISCORD_BOT_TOKEN")
client = commands.Bot(command_prefix='$')

audiofile_path = "./audiofiles/"

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
async def allmemes(ctx):
    """ Returns a list of all memes saved in user's guild """

    guild_id = str(ctx.guild.id)

    allMemes = mongo_storage.get_all_objects(guild_id)

    if not allMemes:
        await ctx.send(
            """
            There are no memes in your collection. 
            You can add memes by using the $addmeme command
            """
        )
        return

    message = "Here are the memes you've added so far: \n\n"
    for post in allMemes:
        message += f"${post.get('name')}\n"

    await ctx.send(message)


@client.command()
async def addmeme(ctx, memeName, url, start, end):
    """
    Command for adding memes.
    - Downloads audio from youtube
    - Trims audio file to the provided start and end timestamps
    - Converts audio file to ogg
    - Uploads file to GCS and cleans up remaining files
    """
    
    newMeme = meme.Meme(ctx, memeName=memeName, url=url, start=start, end=end, audiofile_path=audiofile_path)
    await newMeme.store_me()


@client.command()
async def delete(ctx, memeName):
    """ Deletes meme from MongoDB and GCS. """

    memeToDelete = meme.Meme(ctx, memeName=memeName)
    await memeToDelete.delete_me()

    
@client.command()
async def m(ctx, memeName):
    """ 
    Command for playing memes.
    Connects to Voice Client, gets fileName from MongoDB and calls play(). 
    """

    try:
        vc = await connect_vc(ctx.message.author.voice.channel)
    except:
        await ctx.send("Could not connect or find Voice Client. Make sure you're in a voice channel to begin with.")
        return

    guild_id = str(ctx.guild.id)
    memeToPlay = mongo_storage.get_one_object(guild_id, memeName)
    if not memeToPlay:
        await ctx.send("This meme is not in the database. Use \"$allmemes\" command for all memes or \"$addmeme\" to register a new meme.")
        return

    fullFileName = memeToPlay.get("filename")

    queue.add_element(guild_id, fullFileName)

    if not os.path.exists(f"{audiofile_path}{guild_id}"):
        os.mkdir(f"{audiofile_path}{guild_id}")

    play(ctx, guild_id, vc)


def play(ctx, guild_id, vc):
    """ Downloads and plays a given meme from GCS. """

    def after_handler(error):
        """ Function for handling what happens after playing. """

        if error:
            print(error)
            ctx.send("An error has ocurred: ", error)
            pass
        
        queue.remove_current(guild_id)
        
        currentElementInQueue = queue.get_current(guild_id)
        if not currentElementInQueue:
            try:
                print(f"DELETING: {audiofile_path}{guild_id}")
                shutil.rmtree(f"{audiofile_path}{guild_id}")
                print("Done with queue")
                return
            except Exception as e:
                print(f"Error: ", e)
                return

        play(ctx, guild_id, vc)

    currentElementInQueue = queue.get_current(guild_id)

    with temp_ctx_manager.make_tempfile(f"{audiofile_path}{guild_id}") as tempFileDir:
        GCS.download_blob(currentElementInQueue, tempFileDir)
        audioSource = discord.FFmpegPCMAudio(tempFileDir, options="-f s16le -acodec pcm_s16le")
        if not vc.is_playing():
            vc.play(audioSource, after=after_handler)


async def connect_vc(channel): 
    """ Connects to Voice Client if not already connected and returns it. """

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