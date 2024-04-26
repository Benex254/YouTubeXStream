import json
import subprocess
import sys
from kivymd.app import MDApp
from kivy.clock import Clock,mainthread
from kivy.lang import Builder
from kivy.storage.jsonstore import JsonStore
from kivy.properties import NumericProperty,ListProperty
from kivy.utils import format_bytes_to_human
from queue import Queue
from threading import Thread
from kivy.resources import resource_find
import tempfile
import os
import requests
from utils import move_file,write_crash
temp_dir = tempfile.TemporaryDirectory()


release_url = "https://api.github.com/repos/bxw-855/YouTubeXStream/releases/latest"
app_name = "YouTubeXStream"

def get_temp_path(basename):
    return os.path.join(temp_dir.name,basename)

class UpdateApp(MDApp):
    jobs = NumericProperty(0)
    assets = ListProperty()
    # ---------- init setup ----------- #
    def worker(self,queue:Queue):
        while True:
            job = queue.get()
            job()
            queue.task_done()

    def on_start(self):
        # init worker
        self.queue = Queue()
        self.worker_thread = Thread(target=self.worker,args=(self.queue,)) 
        self.worker_thread.daemon = True
        self.worker_thread.start()
        # init update
        Clock.schedule_once(lambda _:self.get_latest())

    def get_latest(self):
        self.release = requests.get(release_url).json()
        self.assets = self.release["assets"]
        self.ui.ids.title.text = f"Updating to version {self.release["tag_name"]}"
        self.ui.ids.author_avatar.source = self.release["author"]["avatar_url"]
        # self.ui.ids.published_at.text = self.release["published_at"]
    def on_assets(self,instance,assets):
        for asset in assets:
            self.jobs += 1
            download_job = lambda:self.download(
                asset["browser_download_url"],
                asset,
                output_path=get_temp_path(asset["name"])
                )
            self.queue.put(download_job)

    def download(self,url:str,data:dict,output_path=None):
        self.new_download(url)
        current_size = 0
        chunk_size = 8*1024
        total_size = data["size"]
        stream = requests.get(url,
                     headers={
                         "User-Agent":"YouTubeXStream"
                     },
                     stream=True,
                     )
        try:
            with open(output_path,"wb") as file:
                        for chunk in stream.iter_content(chunk_size=chunk_size):
                            if chunk:
                                file.write(chunk)
                                current_size += chunk_size
                                self.on_download_progress(stream,current_size,total_size)
            self.completed_download(stream,data,output_path)
        except Exception as e:
            self.update_failure(stream,e)
    @mainthread
    def new_download(self,url):
        self.ui.ids.asset.text = url
        self.ui.ids.update_progress_label.text = "downloading..."
        self.ui.ids.update_progress.value = 0
    @mainthread
    def on_download_progress(self,stream,current_size,total_size):        
        self.ui.ids.update_progress_label.text = f"{format_bytes_to_human(current_size)}/{format_bytes_to_human(total_size)}" 
        percentage_completion  = (current_size/total_size)*100
        self.ui.ids.update_progress.value = percentage_completion

    # fired when [ failure || redirect || error ]
    @mainthread
    def update_failure(self,req,reason):
        self.exit_updater(f"Failed update\n{reason}\nYou can exit to try and update again later")    
    @mainthread
    def completed_download(self,stream,data:dict,source):
        dest_path = os.path.join(".")
        dest_path_ = os.path.join(".",data["name"])
        if os.path.exists(dest_path_):
            os.remove(dest_path_)
        job = lambda:self.install(source,dest_path,data) 
        self.queue.put(job)
        
    def install(self,source,dest_path,data):
        self.ui.ids.job_type.text = "Installing:"
        self.ui.ids.asset.text = data["browser_download_url"]
        try:
            move_file(source,dest_path)
        except Exception as e:
            self.exit_updater(f"Failed update\n{e}\nYou can exit to try and update again later")
        self.jobs-=1
    
    def exit_updater(self,result):
        self.ui.current = "completed_screen"
        self.ui.ids.update_result.text = result
    
    def on_jobs(self,instance,value):
        if value==0:
            self.update_complete()

    @mainthread
    def update_complete(self):
        with open("./release.json","w") as file:
            j = json.dumps(self.release)
            file.write(j)
        self.exit_updater(f"Update Complete,You can Now close this window")

    def build(self):
        self.user_settings = JsonStore("user_settings.json")
        try:
            color = self.user_settings.get("theme")["color"]
            style = self.user_settings.get("theme")["style"]
        except:
            color = "Silver"
            style = "Dark"
        self.theme_cls.primary_palette = color
        self.theme_cls.theme_style = style
        self.ui = Builder.load_file("./ui/update.kv")
        self.title = app_name
        return self.ui

    def on_stop(self,*args):
        super(UpdateApp,self).on_stop(*args)
        try:
            subprocess.call(resource_find("YouTubeXStream.exe"))
        except Exception as e:
            index = write_crash(e)
                   
if __name__ == "__main__":
    try:
        UpdateApp().run()
    except Exception as e:
        index =  write_crash(e)
        try:
            args = ["Failed_Update", f"\"{index}\""]
            cmd = [resource_find("YouTubeXStream.exe")]+args
            subprocess.call(cmd)
            
        except Exception as e:
            index = write_crash(e)