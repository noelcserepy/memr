# What is Memr?
Memr is a Discord bot that allows members of a Discord server to save short audio clips from YouTube as memes and recall them with a command. 



## Installation
This bot is still in development. If you are interested, send me a PM on GitHub and I will let you know when Memr is ready to be tested.



## How does it work?
After the bot is added to your Discord channel, the bot's database is a blank slate. This means that there are no memes saved yet. 


### Adding memes
You can add memes to the database by typing the command "$addmeme" in the discord chat, followed by the name of your meme, the youtube link and the start and end timestamps.

Example: 
`$addmeme rickroll https://www.youtube.com/watch?v=dQw4w9WgXcQ 0:42.5 0:51`

A meme can be a maximum of 10 seconds long. 


### Playing memes
To play the meme just use the command "$meme" followed by the name of the meme you would like to recall. 

Example:
`$meme rickroll`

The Memr bot will then enter the voice channel you are currently in and play the audio clip. 


### Other commands

`$remove memeName` - Will remove a meme from the database. 

`$join` - Will make Memr join your current voice channel.

`$leave` - Will make Memr leave your current voice channel. 



## Why I built this bot
When I talk with my friends, we often reference funny videos throughout our conversation. We would repeat what we heard in videos, calling to everyone's minds the feel and sentiment of a given video. Audio memes have become part of our language and our humour, just like gifs and emojis are part of text messages and emails. I therefore often wished that playing audio memes in realtime conversation was as easy as adding an emoji to a text message. Even if the visual component is missing, audio brings the video to mind, along with the emotions and message of the original. 

Image memes and video memes are prevalent throughout the internet today but audio memes have not really taken off. I think that is not because audio memes are inherently flawed, but because there are a lack of platforms that support it, including real life. You would be hard pressed to find someone carrying around a sound board everywhere they go. Since many of our conversations - especially now - happen online anyways, I figured that nothing really stands in the way of making my wish come true. 

I am very excited for this project because it allows every group of friends to create their own personal repository of audio in-jokes that can seamlessly be inserted into every conversation. With that, I hope it brings as much joy to you as it does to me!