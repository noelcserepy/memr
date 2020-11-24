import os
import asyncio
from collections import deque
from errors.errors import TempCleanerError



class TempCleaner():
    def __init__(self, client, audiofile_path):
        self.client = client
        self.audiofile_path = audiofile_path
        self.loop = asyncio.get_event_loop()
        self.paths_to_delete = deque([])
        self.delete_all_temps()

        client.temp_clean_task = self.loop.create_task(self.clean_temp_task())


    def delete_all_temps(self):
        temps_to_delete = os.listdir(self.audiofile_path)
        for temp in temps_to_delete:
            path = os.path.join(self.audiofile_path, temp)
            print("rmtree", path)
            # shutil.rmtree(path)

    
    def flag_to_remove(self, path):
        self.paths_to_delete.append(path)

        
    async def clean_temp_task(self):
        await self.client.wait_until_ready()

        while not self.client.is_closed():
            print(self.paths_to_delete)
            for i in range(len(self.paths_to_delete)):
                path_to_delete = self.paths_to_delete.popleft()
                os.remove(path_to_delete)
            await asyncio.sleep(5)


            # Remove directories method. maybe?
            # temp_dirs = os.listdir(audiofile_path)
            # if temp_dirs:
            #     for guild_temp in temp_dirs:
            #         vc = discord.utils.find(lambda vc: vc.guild.id == guild_temp, client.voice_clients)
            #         print(vc)
            #         if vc:
            #             if vc.is_playing():
            #                 continue
            #             shutil.rmtree(f"{audiofile_path}{guild_temp}")