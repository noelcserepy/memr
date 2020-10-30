import discord
from discord.ext import commands

import os
import uuid
import re

from tinydb import TinyDB, Query
import util.helpers
import util.audio_tools
import storage.mongo_storage
import storage.GCS


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

    timecode_valid = helpers.check_valid_timecode(memeName, start, end)

    if not type(timecode_valid) == int:
        await ctx.send(timecode_valid)

    guild_id = str(ctx.guild.id)
    stored_meme = mongo_storage.get_one_object(guild_id, memeName)
    if stored_meme:
        await ctx.send("Meme name already exists. Try again.")
        return

    memeID = uuid.uuid1().hex
    fileName = memeID + " - " + memeName

    try:
        audio_tools.download_convert(url, fileName, start, end, audiofile_path)
    except:
        print("Download and/or conversion failed")
        await ctx.send("Download and/or conversion failed")
        return

    saved_in_mongo = mongo_storage.save_object(guild_id, memeName, fileName, start, end)
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

    guild_id = str(ctx.guild.id)
    docToPlay = mongo_storage.get_one_object(guild_id, memeName)
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
    collection = db[str(ctx.guild.id)]
    docToRemove = collection.find_one({"name": memeName})

    if not docToRemove:
        await ctx.send("This meme is not in the database. Use \"$allmemes\" command for all memes.")
        return
    
    memePath = docToRemove.get("path")

    if os.path.exists(memePath):
        os.remove(memePath)
        print(f"Removed audio file for \"{memeName}\".")

    docToRemove_id = docToRemove.get("_id")
    collection.delete_one({"_id": docToRemove_id})
    
    await ctx.send(f"Removed \"{memeName}\" from DB.")


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