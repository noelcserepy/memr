import discord
from discord.ext import commands

import os
import uuid
import re
import tempfile
import shutil
import asyncio

from util import meme_queue, temp_ctx_manager
from storage import GCS, mongo_storage
from meme.meme import Meme, create_meme
from errors.errors import PlayError



discordToken = os.getenv("DISCORD_BOT_TOKEN")
client = commands.Bot(command_prefix='$')

audiofile_path = "./temp/"

@client.event
async def on_ready():
    print(f"Logged in as {client}")


@client.command()
async def join(ctx):
    senderVoiceChannel = ctx.message.author.voice.channel
    await senderVoiceChannel.connect(timeout=30.0, reconnect=True)


@client.command()
async def leave(ctx):
    if ctx.voice_client:
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
    
    newMeme = await create_meme(ctx, memeName, url=url, start=start, end=end, audiofile_path=audiofile_path)
    await newMeme.store()


@client.command()
async def delete(ctx, memeName):
    """ Deletes meme from MongoDB and GCS. """

    memeToDelete = await create_meme(ctx, memeName)
    await memeToDelete.delete()

    
@client.command()
async def m(ctx, memeName):
    """ 
    Connect to voice channel
    Make Meme
    If queue exists for guild, add Meme to queue
    Else make new queue, add Meme to queue and play 
    """

    try:
        vc = await connect_vc(ctx.message.author.voice.channel)
        
        meme_to_play = await create_meme(ctx, memeName)

        in_db = await meme_to_play.is_in_db()
        if not in_db:
            await ctx.send("This meme is not in the database. Use \"$allmemes\" command for all memes or \"$addmeme\" to register a new meme.")
            return

        meme_queue.add_element(meme_to_play)

        #put in temp_ctx_manager
        if not os.path.exists(f"{audiofile_path}{meme_to_play.guild_id}"):
            os.mkdir(f"{audiofile_path}{meme_to_play.guild_id}")

        await play(meme_to_play, vc)
    except Exception as ex:
        try:
            print("Error: ", ex)
            await ctx.send("Something went wrong while playing. Try again.")
        except Exception as e:
            print("Error: ", e)


async def play(meme, vc):
    """ Downloads and plays a given meme from GCS. """

    currentElementInQueue = meme_queue.get_current(meme.guild_id)

    # fix this
    with temp_ctx_manager.make_tempfile(f"{audiofile_path}{meme.guild_id}") as tempFileDir:
        await GCS.download_blob(currentElementInQueue.fileName, tempFileDir)
        audioSource = discord.FFmpegPCMAudio(tempFileDir, options="-f s16le -acodec pcm_s16le")

        if not vc.is_playing():
            vc.play(audioSource, after=after_handler)


    def after_handler(error):
        """ Function for handling what happens after playing. """

        if error:
            raise PlayError("After handler Failed.")

        coro = play_next_in_queue(meme, vc)
        fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
        try:
            fut.result()
        except:
            print("After handler failed.")
            pass

    
async def play_next_in_queue(meme, vc):
    next_meme = meme_queue.next(meme)
    
    if not next_meme:
        print(f"DELETING: {audiofile_path}{meme.guild_id}")
        shutil.rmtree(f"{audiofile_path}{meme.guild_id}")
        print("Done with queue")
        return

    play(meme, vc)


async def connect_vc(channel): 
    """ Connects to Voice Client if not already connected and returns it. """
    try: 
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
    except:
        try:
            await ctx.send("Could not connect or find Voice Client. Make sure you're in a voice channel to begin with.")
        except:
            print("Voice client could not connect")
            return


client.run(discordToken)