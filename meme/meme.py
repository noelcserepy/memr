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


    def mongo_exists(self):
        stored_meme = mongo_storage.get_one_object(self.guild_id, self.memeName)
        if stored_meme:
            return True
    

    def mongo_add(self):
        try:
            memeData = {
                "name": self.memeName, 
                "filename": self.fileName,
                "start": self.startSeconds,
                "end": self.endSeconds,
                "youtubeUrl": self.url
            }

            saved_in_mongo = mongo_storage.save_object(self.guild_id, memeData)
            if not saved_in_mongo:
                raise errors.MongoError(f"Saving {self.memeName} to database failed. Please try again.")
        except Exception as e:
            print(f"Error: ", e)


    def mongo_get(self):
        memeObj = mongo_storage.get_one_object(self.guild_id, self.memeName)
        return memeObj


    def mongo_remove(self):
        pass



    def GCS_exists(self):
        try:
            if not self.fileName:
                memeObj = self.mongo_get()
                self.fileName = memeObj.get("filename")
            exists = GCS.blob_exists(self.fileName)
            return exists
        except Exception as e:
            print("Error: ", e)


    def GCS_add(self):
        try:
            oggExists = os.path.exists(f"{self.audiofile_path}{self.fileName}")

            if oggExists:
                GCS.upload_blob(f"{self.audiofile_path}{self.fileName}")
                os.remove(f"{self.audiofile_path}{self.fileName}")
            else:
                print("GCS_add() - ogg doesn't exist")
        except Exception as e:
                print(f"Error: {e}")


    def GCS_get(self):
        pass


    def GCS_remove(self):
        pass


    
    def add_to_queue(self):
        pass


    def play(self):
        pass


    def convert_timecodes(self):
        try:
            valid_timecodes = timecode.check_valid_timecode(self.memeName, self.start, self.end)
            self.startSeconds = valid_timecodes[0]
            self.endSeconds = valid_timecodes[1]
        except Exception as e:
            print("Error: ", e)


    def make_memeTag_and_fileName(self):
        if not self.memeTag and not self.fileName:
            memeID = uuid.uuid1().hex
            self.memeTag = memeID + " - " + self.memeName
            self.fileName = self.memeTag + ".ogg"
    


    def download_audio(self):
        try:
            yt = YouTube(self.url)
            saved = yt.streams.get_audio_only().download(output_path=self.audiofile_path, memeTag=self.memeTag)
            
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

            mp4Exists = os.path.exists(f"{self.audiofile_path}{self.memeTag}.mp4")
            if mp4Exists:
                os.remove(f"{self.audiofile_path}{self.memeTag}.mp4")
            else:
                print("mp4 doesn't exist.")
        except Exception as e:
            print(f"Error: {e}")

    
    def store_me(self):
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
                raise errors.MissingArguments("store_me() was called without providing the correct arguments")
                
            if self.mongo_exists():
                raise errors.MongoError("Meme already exists in MongoDB")

            self.convert_timecodes()
            self.make_memeTag_and_fileName()
            self.download_audio()
            self.mongo_add()
            self.GCS_add()

            await self.ctx.send(f"\"{self.memeName}\" meme has been added to your collection! Use it with the command \"$m {self.memeName}\"")
        except Exception as e:
            print("Error: ", e)