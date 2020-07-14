import discord
import os
import re

client = discord.Client()

@client.event
async def on_ready():
    print(f"Logged in as {client}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return


    if message.content.startswith("!meme "):
        print(message.content)
        memeReq = re.search(r"\!meme (.+)", message.content).group(1)
        await message.channel.send(memeReq)


    if message.content.startswith("$hello"):
        await message.channel.send("hello!")

    if message.content == "who":
        sender = message.author
        senderVoiceChannel = sender.voice.channel
        await senderVoiceChannel.connect(timeout=60.0, reconnect=True)




token = os.getenv("DISCORD_BOT_TOKEN")
client.run(token)