import time
import ffmpeg 
from pytube import YouTube

def download_convert(url, fileName, start, end, audiofile_path):
    yt = YouTube(url)
    saved = yt.streams.get_audio_only().download(output_path=audiofile_path, filename=fileName)
    
    sleptFor = 0
    while not saved:
        time.sleep(1)
        sleptFor += 1
        if sleptFor > 20:
            raise Exception("Timeout while downloading")
            
    stream = ffmpeg.input(f"{audiofile_path}{fileName}.mp4")
    stream = stream.audio.filter("atrim", start=start, end=end)
    stream = ffmpeg.output(stream, f"{audiofile_path}{fileName}.ogg")
    ffmpeg.run(stream)

