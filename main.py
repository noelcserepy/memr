import discord
import os
import re
import youtube_dl
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


# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return


#     if message.content.startswith("!meme "):
#         print(message.content)
#         memeReq = re.search(r"\!meme (.+)", message.content).group(1)
#         await message.channel.send(memeReq)


#     if message.content.startswith("$hello"):
#         await message.channel.send("hello!")

#     if message.content == "who":
#         sender = message.author
#         senderVoiceChannel = sender.voice.channel
#         currentVoiceClient = await senderVoiceChannel.connect(timeout=60.0, reconnect=True)

#         currentAudioSource = discord.AudioSource.read("audiofiles/pusstime.ogg")
#         currentVoiceClient.play(currentAudioSource)





client.run(token)


# def custom_probe(source, executable):
#     # some analysis code here

#     return codec, bitrate

# source = await discord.FFmpegOpusAudio.from_probe("song.webm", method=custom_probe)
# voice_client.play(source)