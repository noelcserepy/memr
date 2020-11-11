import discord
import uuid
import os
import time
import ffmpeg

from pytube import YouTube
from errors import errors
from storage import GCS, mongo_storage
from util import timecode, queue, temp_ctx_manager

class Meme():
    def __init__(self, ctx, memeName=None, url=None, start=None, end=None, audiofile_path=None):
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
    

    def mongo_add(self):
        memeData = {
            "name": self.memeName, 
            "filename": self.fileName,
            "start": self.startSeconds,
            "end": self.endSeconds,
            "youtubeUrl": self.url
        }

        mongo_storage.save_object(self.guild_id, memeData)


    def mongo_get(self):
        memeObj = mongo_storage.get_one_object(self.guild_id, self.memeName)
        if not memeObj:
            raise errors.MongoError("mongo_get() - Could not get storage object.")

        self.fileName = memeObj.get("filename")
        self.startSeconds = memeObj.get("start")
        self.endSeconds = memeObj.get("end")
        self.url = memeObj.get("youtubeUrl")
        self.mongoID = memeObj.get("_id")

        return memeObj


    def convert_timecodes(self):
        valid_timecodes = timecode.check_valid_timecode(self.memeName, self.start, self.end)
        self.startSeconds = valid_timecodes[0]
        self.endSeconds = valid_timecodes[1]
        

    def make_memeTag_and_fileName(self):
        if not self.memeTag and not self.fileName:
            memeID = uuid.uuid1().hex
            self.memeTag = memeID + " - " + self.memeName
            self.fileName = self.memeTag + ".ogg"
    

    def download_audio(self):
        yt = YouTube(self.url)
        saved = yt.streams.get_audio_only().download(output_path=self.audiofile_path, filename=self.memeTag)
        
        sleptFor = 0
        while not saved:
            time.sleep(1)
            sleptFor += 1
            if sleptFor > 20:
                raise errors.YTDownloadError("Timeout while downloading")
                
        stream = ffmpeg.input(f"{self.audiofile_path}{self.memeTag}.mp4")
        stream = stream.audio.filter("atrim", start=self.startSeconds, end=self.endSeconds)
        stream = ffmpeg.output(stream, f"{self.audiofile_path}{self.memeTag}.ogg")
        ffmpeg.run(stream)

        oggExists = os.path.exists(f"{self.audiofile_path}{self.memeTag}.ogg")
        mp4Exists = os.path.exists(f"{self.audiofile_path}{self.memeTag}.mp4")

        if mp4Exists:
            os.remove(f"{self.audiofile_path}{self.memeTag}.mp4")
        else:
            raise errors.AudioConversionError("Mp4 not found. Deletion failed.")
        if not oggExists:
            raise errors.AudioConversionError("Ogg not found. Conversion failed.")
        

    
    async def store_me(self):
        try:
            values = [
                self.ctx,
                self.memeName,
                self.url,
                self.start,
                self.end,
                self.audiofile_path
            ]

            if not all(v is not None for v in values):
                raise errors.MissingArguments("store_me() was called on Meme object without the correct class variables.")
                
            if mongo_storage.get_one_object(self.guild_id, self.memeName):
                raise errors.MongoError("Meme already exists in MongoDB.")

            self.convert_timecodes()
            self.make_memeTag_and_fileName()
            self.download_audio()
            self.mongo_add()
            GCS.upload_blob(self.audiofile_path, self.fileName)
            os.remove(f"{self.audiofile_path}{self.fileName}")

            await self.ctx.send(f"""
            \"{self.memeName}\" meme has been added to your collection! Use it with the command \"$m {self.memeName}\"""")
        except Exception as e:
            print("Error: ", e)
            try:
                self.cleanup()
            except Exception as e:
                print("Error: ", e)


    def cleanup(self):
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
        if GCS.blob_exists(self.fileName):
            GCS.delete_blob(self.fileName)

        # Mongo
        if mongo_storage.get_one_object(self.guild_id, self.memeName):
            mongo_storage.delete_object(self.guild_id, self.mongoID)
    

    async def delete_me(self):
        try:
            values = [
                self.ctx,
                self.memeName
            ]

            if not all(v is not None for v in values):
                raise errors.MissingArguments("store_me() was called on Meme object without the correct class variables.")
                
            if not mongo_storage.get_one_object(self.guild_id, self.memeName):
                await self.ctx.send("This meme is not in the database. Use \"$allmemes\" command to see all memes you have saved.")

            self.mongo_get()
            try:
                GCS.delete_blob(self.fileName)
            except Exception as e:
                print("No GCS object was found when deleting. Carrying on...")
            try:
                mongo_storage.delete_object(self.guild_id, self.mongoID)
            except Exception as e:
                print("No MongoDB object was found when deleting. Carrying on...")

            await self.ctx.send(f"Removed \"{self.memeName}\" from your collection.")
        except Exception as e:
            print("Error: ", e)


    def add_to_queue(self):
        pass


    def play_me(self):
        pass
