import discord
from discord.ext import commands

import os
import uuid
import re
import tempfile
import shutil
import asyncio

from util import meme_queue,temp_cleaner
from storage import GCS, mongo_storage
from meme.meme import Meme, create_meme
from errors.errors import PlayError, EmptyError, VCError



discordToken = os.getenv("DISCORD_BOT_TOKEN")
client = commands.Bot(command_prefix='$')

audiofile_path = "./temp/"

temp_cleaner_instance = temp_cleaner.TempCleaner(client, audiofile_path)

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
    all_memes = await mongo_storage.get_all_objects(guild_id)
    
    if not all_memes:
        await ctx.send(
            """
            There are no memes in your collection. 
            You can add memes by using the $addmeme command
            """
        )
        return

    all_meme_names = [post.get("name") for post in all_memes]
    sorted_meme_names = sorted(all_meme_names, key=str.lower)

    message = "Here are the memes you've added so far: \n\n"
    for meme_name in sorted_meme_names:
        message += f"${meme_name}\n"

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
        vc = await connect_vc(ctx)
        meme_to_play = await create_meme(ctx, memeName)

        in_db = await meme_to_play.is_in_db()
        if not in_db:
            await ctx.send("This meme is not in the database. Use \"$allmemes\" command for all memes or \"$addmeme\" to register a new meme.")
            return

        meme_queue.add_element(meme_to_play)

        if not os.path.exists(f"{audiofile_path}{meme_to_play.guild_id}"):
            os.mkdir(f"{audiofile_path}{meme_to_play.guild_id}")

        await play(meme_to_play, vc)
    except VCError:
        try:
            await ctx.send("Could not connect to voice client. Make sure you're in a voice channel.")
        except Exception as e:
            print("Error: ", e)
    except Exception as ex:
        try:
            print("Error: ", ex)
            await ctx.send("Something went wrong while playing. Try again.")
        except Exception as e:
            print("Error: ", e)


async def play(meme, vc):
    """ Downloads and plays a given meme from GCS. """

    def after_handler(error):
        """ Function for handling what happens after playing. """
        try:
            if error:
                raise PlayError(error)
            
            temp_cleaner_instance.flag_to_remove(tempFileDir)

            coro = play_next_in_queue(meme, vc)
            fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
            fut.result()
        except EmptyError:
            print("Queue is done.")
        except Exception as e:
            print("After handler failed.", e)
            pass

    currentElementInQueue = meme_queue.get_current(meme)
    if not currentElementInQueue:
        raise EmptyError()

    temp_path = f"{audiofile_path}{meme.guild_id}"
    _, tempFileDir = tempfile.mkstemp(suffix=".ogg", dir=temp_path)

    await GCS.download_blob(currentElementInQueue.fileName, tempFileDir)

    audioSource = discord.FFmpegPCMAudio(tempFileDir, options="-f s16le -acodec pcm_s16le")

    if not vc.is_playing():
        vc.play(audioSource, after=after_handler)

    
async def play_next_in_queue(meme, vc):
    meme_queue.next(meme)
    await play(meme, vc)


async def connect_vc(ctx): 
    """ Connects to Voice Client if not already connected and returns it. """
    try: 
        channel = ctx.message.author.voice.channel
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
        raise VCError("Voice client could not connect")


client.run(discordToken)