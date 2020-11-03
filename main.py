import discord
from discord.ext import commands

import os
import uuid
import re

from tinydb import TinyDB, Query
from util import helpers
from util import audio_tools
from storage import mongo_storage
from storage import GCS
from errors import errors


# Instantiate Discord API client
discordToken = os.getenv("DISCORD_BOT_TOKEN")
client = commands.Bot(command_prefix='$')

audiofile_path = "../audiofiles/"

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
    """
    Returns a list of all memes saved in user's guild
    """
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

    - Checks if inputs are correct
    - Checks if meme already exists in database
    - Downloads audio from youtube
    - Trims audio file to the provided start and end timestamps
    - Converts audio file to ogg 
    - Uploads file to GCS and cleans up remaining files
    """

    try:
        timecode_valid = helpers.check_valid_timecode(memeName, start, end)
    except:
        await ctx.send("Invalid timestamps. Try again")

    guild_id = str(ctx.guild.id)
    stored_meme = mongo_storage.get_one_object(guild_id, memeName)
    if stored_meme:
        await ctx.send("Meme name already exists. Try again.")
        return

    memeID = uuid.uuid1().hex
    fileName = memeID + " - " + memeName
    startSeconds = timecode_valid[0]
    endSeconds = timecode_valid[1]

    try:
        audio_tools.download_convert(url, fileName, startSeconds, endSeconds, audiofile_path)
    except errors.AudioConversionError as e:
        print(e)
        await ctx.send("Download and/or conversion failed")
        return

    saved_in_mongo = mongo_storage.save_object(guild_id, memeName, fileName, startSeconds, endSeconds, url)
    if not saved_in_mongo:
        await ctx.send(f"Saving {memeName} to database failed. Please try again.")

    mp4Exists = os.path.exists(f"{audiofile_path}{fileName}.mp4")
    oggExists = os.path.exists(f"{audiofile_path}{fileName}.ogg")

    if oggExists:
        try:
            GCS.upload_blob(f"{audiofile_path}{fileName}.ogg")
            os.remove(f"{audiofile_path}{fileName}.ogg")
        except:
            raise Exception("File could not be uploaded to GCS")
            return
    else:
        print("ogg doesn't exist")

    if mp4Exists:
        os.remove(f"{audiofile_path}{fileName}.mp4")
    else:
        print("mp4 doesn't exist.")

    await ctx.send(f"\"{memeName}\" meme has been added to your collection! Use it with the command $meme {memeName}")


@client.command()
async def m(ctx, memeName):
    """
    Recalls meme with chosen name argument.
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


    # Function for handling what happens after playing.
    def afterHandler(error):
        if error:
            print(error)
            ctx.send("An error has ocurred: ", error)
            pass

        nextElement = helpers.queue_get_next(guild_id)

        if not nextElement:
            print("Done with queue.")
            return
        else:
            play(guild_id, vc, afterHandler, fileName, audiofile_path)


    fileName = memeToPlay.get("filename")

    play(guild_id, vc, afterHandler, fileName, audiofile_path)

    


@client.command()
async def delete(ctx, memeName):
    guild_id = str(ctx.guild.id)
    memeToDelete = mongo_storage.get_one_object(guild_id, memeName)
    if not memeToDelete:
        await ctx.send("This meme is not in the database. Use \"$allmemes\" command to see all memes you have saved.")
        return

    memeObjName = memeToDelete.get("filename")
    memeExists = GCS.blob_exists(memeObjName)

    if memeExists:
        GCS.delete_blob(memeObjName)
        print(f"Removed {memeObjName} from GCS")

    memeObjID = memeToDelete.get("_id")
    deleted = mongo_storage.delete_object(guild_id, memeObjID)

    if not deleted:
        ctx.send(f"Could not remove \"{memeObjName}\" from database.")
    
    await ctx.send(f"Removed \"{memeName}\" from DB.")


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
    

def play(guild_id, vc, afterHandler, fileName, audiofile_path):
    filePath = f"{audiofile_path}{fileName}"

    try:
        GCS.download_blob(fileName, audiofile_path)
    except Exception as e:
        print(f"Error: {e}")
        
    try:
        if not vc.is_playing():
            vc.play(discord.FFmpegPCMAudio(filePath), after=afterHandler)
        else:
            helpers.queue_add_element(guild_id, fileName)
    except Exception as e:
        print(f"Playback Error: {e}")

    try:
        os.remove(f"{audiofile_path}{fileName}.ogg")
    except Exception as e:
        print(f"Error: {e}")


client.run(discordToken)