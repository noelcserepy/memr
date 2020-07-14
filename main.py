import discord
import os

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
        return


    if message.content.startswith("$hello"):
        await message.channel.send("hello!")


token = os.getenv("DISCORD_BOT_TOKEN")
client.run(token)