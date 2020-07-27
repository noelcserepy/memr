import discord
import os
import re
from pytube import YouTube
import ffmpeg 
import time
import uuid
from discord.ext import commands
from tinydb import TinyDB, Query



def convertTime(a):
    if not re.match(r"^[0-9:.]+$", a):
        return "invalid timecode"
        
    b = a.split(":")
    
    if len(b) == 1:
        return a
    
    if len(b) == 2:
        if "." in b[0]:
            return "No decimals in the minutes pls"

        if int(b[0]) >= 60:
            return "Can't have more than 60 minutes in an hour, dummy."

        if float(b[1]) >= 60:
            return "Can't have more than 60 seconds in a minute, dummy."

        mins = int(b[0]) * 60
        secs = float(b[1]) 
        return mins + secs
    
    if len(b) == 3:
        if "." in b[0]:
            return "No decimals in the hours pls"
        
        if int(b[0]) > 5:
            return "That's a really long video. I am not bothering to download that."

        if "." in b[1]:
            return "No decimals in the minutes pls"

        if int(b[1]) >= 60:
            return "Can't have more than 60 minutes in an hour, dummy."

        if float(b[2]) >= 60:
            return "Can't have more than 60 seconds in a minute, dummy."

        hrs = int(b[0]) * 60 * 60
        mins = int(b[1]) * 60
        secs = float(b[2])
        return hrs + mins + secs

#print(convertTime("1:2:20.2"))

# from datetime import datetime
# import time
# s = "09:51:43.22"
# s = "16/09/1990 " + s 
# d = datetime.strptime(s, "%d/%m/%Y  %H:%M:%S.%f")
# secs = time.mktime(d.timetuple())
# print(secs)

l = [12345]

if (1 or -1) == -1:
    print("yee")
else: 
    print("Nope")