import discord
import uuid
import os
import time
import ffmpeg
import asyncio

from pytube import YouTube
from errors.errors import MissingArguments, YTDownloadError, AudioConversionError, TimecodeError, MemrError
from storage import GCS, mongo_storage
from util import timecode



async def create_meme(ctx, memeName, url=None, start=None, end=None, audiofile_path=None):
    """ Function to instantiate a new Meme object asynchronously. """

    new_meme = Meme(ctx, memeName, url=url, start=start, end=end, audiofile_path=audiofile_path)
    await new_meme.mongo_get()
    return new_meme


class Meme():
    def __init__(self, ctx, memeName, url=None, start=None, end=None, audiofile_path=None):
        self.ctx = ctx
        self.memeName = memeName
        self.url = url
        self.start = start
        self.end = end
        self.audiofile_path = audiofile_path
        self.guild_id = str(ctx.guild.id)

        self.fileName = None
        self.memeTag = None
        self.startSeconds = None
        self.endSeconds = None
        self.mongoID = None
        self.failed_getting = False
    

    def check_inputs(self, values):
        for v in values:
            print(v)
        if not all(v is not None for v in values):
            raise MissingArguments("Called Meme method without the correct class variables.")

    async def is_in_db(self):
        try:
            if self.mongoID:
                return True
            
            if not self.failed_getting:
                return False

            # timeout = 0
            # while self.failed_getting:
            #     await self.mongo_get()

            #     if self.mongoID:
            #         return True

            #     await asyncio.sleep(1)
            #     timeout += 1
            #     if timeout >= 5:
            #         raise TimeoutError("Timed out while fetching MongoDB data.")
        except:
            raise 


    def convert_timecodes(self):
        valid_timecodes = timecode.check_valid_timecode(self.memeName, self.start, self.end)
        self.startSeconds = valid_timecodes[0]
        self.endSeconds = valid_timecodes[1]
        

    async def download_audio(self):
        yt = YouTube(self.url)
        saved = yt.streams.get_audio_only().download(output_path=self.audiofile_path, filename=self.memeTag)
        
        sleptFor = 0
        while not saved:
            await asyncio.sleep(1)
            sleptFor += 1
            if sleptFor > 20:
                raise YTDownloadError("Timeout while downloading")

        (
            ffmpeg
            .input(f"{self.audiofile_path}{self.memeTag}.mp4")
            .audio.filter("atrim", start=self.startSeconds, end=self.endSeconds)
            .output(f"{self.audiofile_path}{self.memeTag}.ogg")
            .run()
        )    

        oggExists = os.path.exists(f"{self.audiofile_path}{self.memeTag}.ogg")
        mp4Exists = os.path.exists(f"{self.audiofile_path}{self.memeTag}.mp4")

        if mp4Exists:
            os.remove(f"{self.audiofile_path}{self.memeTag}.mp4")
        else:
            raise AudioConversionError("Mp4 not found. Deletion failed.")
        if not oggExists:
            raise AudioConversionError("Ogg not found. Conversion failed.")


    async def mongo_add(self):
        memeData = {
            "name": self.memeName, 
            "filename": self.fileName,
            "start": self.startSeconds,
            "end": self.endSeconds,
            "youtubeUrl": self.url
        }

        await mongo_storage.save_object(self.guild_id, memeData)


    async def mongo_get(self):
        try:
            memeObj = await mongo_storage.get_one_object(self.guild_id, self.memeName)

            self.fileName = memeObj.get("filename")
            self.startSeconds = memeObj.get("start")
            self.endSeconds = memeObj.get("end")
            self.url = memeObj.get("youtubeUrl")
            self.mongoID = memeObj.get("_id")
            self.failed_getting = False

            return memeObj
        except Exception as e:
            self.failed_getting = True
            print("Error in mongo_get: ", e)        

    
    async def store(self):
        try:
            values = [
                self.ctx,
                self.memeName,
                self.url,
                self.start,
                self.end,
                self.audiofile_path
            ]

            self.check_inputs(values)

            in_db = await self.is_in_db()
            if in_db:
                raise MemrError("Meme already exists in MongoDB.")

            self.convert_timecodes()

            memeID = uuid.uuid1().hex
            self.memeTag = memeID + " - " + self.memeName
            self.fileName = self.memeTag + ".ogg"

            await self.download_audio()
            await self.mongo_add()
            await GCS.upload_blob(self.audiofile_path, self.fileName)
            os.remove(f"{self.audiofile_path}{self.fileName}")


            # This runs when mongo.add() fails...
            await self.ctx.send(f"""
            \"{self.memeName}\" meme has been added to your collection! Use it with the command \"$m {self.memeName}\"""")
        except Exception as e:
            print("Error: ", e)
            try:
                await self.reset()
            except Exception as e:
                print("Error: ", e)


    async def reset(self):
        if not self.fileName:
            return

        # files
        oggPath = f"{self.audiofile_path}{self.fileName}"
        mp4Path = f"{self.audiofile_path}{self.memeTag}.mp4"
        if os.path.exists(oggPath):
            os.remove(oggPath)
        if os.path.exists(mp4Path):
            os.remove(mp4Path)

        # GCS
        if await GCS.blob_exists(self.fileName):
            await GCS.delete_blob(self.fileName)

        # Mongo
        if await mongo_storage.get_one_object(self.guild_id, self.memeName):
            await mongo_storage.delete_object(self.guild_id, self.mongoID)
    

    async def delete(self):
        try:
            values = [
                self.ctx,
                self.memeName,
                self.guild_id,
                self.mongoID,
                self.memeName
            ]

            self.check_inputs(values)

            try:
                await GCS.delete_blob(self.fileName)
            except Exception as e:
                print("No GCS object was found when deleting. Carrying on...")
            try:
                await mongo_storage.delete_object(self.guild_id, self.mongoID)
            except Exception as e:
                print("No MongoDB object was found when deleting. Carrying on...")

            await self.ctx.send(f"Removed \"{self.memeName}\" from your collection.")
        except Exception as e:
            print("Error: ", e)


