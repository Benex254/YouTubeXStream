import sys
from kivymd.app import MDApp
from datetime import datetime
from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.snackbar import MDSnackbar,MDSnackbarText,MDSnackbarSupportingText,MDSnackbarButtonContainer,MDSnackbarCloseButton
from kivy.uix.screenmanager import FadeTransition
from kivy.properties import NumericProperty,BooleanProperty,StringProperty,ObjectProperty
from kivy.utils import format_bytes_to_human
from queue import Queue
from threading import Thread
import tempfile
import shutil
import os

temp_dir = tempfile.TemporaryDirectory()
release_url = "https://api.github.com/repos/bxw-855/YouTubeXStream/realeases/latest"

def move_file(source_path,dest_path):
    try:
        path = shutil.move(source_path,dest_path)
        return (1,path)
    except Exception as e:
        return (0,e)
class UpdateApp(MDApp):
    total_downloaded = NumericProperty(0)
    jobs = NumericProperty()
    release = ObjectProperty()
    # ---------- init setup ----------- #
    def worker(self,queue:Queue):
        while True:
            job = queue.get()
            self.download(*job)
            self.jobs -=1
            queue.task_done()

    def on_start(self):
        # init worker
        self.queue = Queue()
        self.worker_thread = Thread(target=self.worker,args=(self.queue,)) 
        self.worker_thread.daemon = True
        self.worker_thread.start()
        # init update
        self.get_latest()
        # os.system.
        success,val = move_file("C:/Program Files/Calibre2/calibre.exe","C:/Program Files/Calibre2/app")
        if success:
            print(val)
        else:
            print(val)
    # --------- get latest release ------------ #
    def get_latest(self):
        url = release_url
        req = UrlRequest(url, self.got_latest,on_error=self.got_latest_error,
                        on_failure = self.got_latest_failure,file_path="./release.json")       
    def got_latest(self,request,result):
        print(result)
        self.release = result
        self.download_latest()
    def got_latest_error(self,request,error):
        print(error)
    def got_latest_failure(self,request,failure):
        print(failure)

    # --------- download latest ------------ #

    def download_latest(self):
        download_jobs = self.extract_assests()
        for job in download_jobs:
            self.add_job(job)
    def extract_assets(self)->list:
        jobs = [("a",release_url,129290),("a",release_url,129290)]
        return jobs
    
    def download(self,name,url,totalsize):
        req = UrlRequest(url,
                         self.downloaded_resource,
                         self.download_redirect,
                         self.download_failure,
                         self.download_error,
                         self.download_progress,
                         req_headers={
                             "User-Agent":"YouTubeXStream"
                         }

                         )
        self.url = url
        self.name = name
        self.totalsize = totalsize
    def download_progress(self,request,current_size,total_size):
        print("progress...")
        print(total_size,current_size)
    def downloaded_resource(self,*args):
        print("complete")
        print(*args)
    def download_failure(self,*args):
        print("failed")
        print(*args)
    def download_error(self,*args):
        print("error")
        print(*args)
    
    def add_job(self,job):
        # self.queue.put(job)
        print(job)
        self.jobs +=1
        print(self.jobs)
    def show_toast(self,title,details):
        def _show(dt):
            MDSnackbar(
                MDSnackbarText(
                    text = title
                ),
                MDSnackbarSupportingText(
                    text = details
                ),
                MDSnackbarButtonContainer(
                    MDSnackbarCloseButton(
                        icon="close"
                    ),
                    pos_hint={"center_y":.5}
                ),
                duration = 3,
                y="10dp",
                pos_hint = {"right":0.99},
                size_hint_x = .4,
                padding="5dp",
                orientation="horizontal"
            ).open()
        Clock.schedule_once(_show)
    def build(self):
        self.user_settings = JsonStore("user_settings.json")

        try:
            color = self.user_settings.get("theme")["color"]
            style = self.user_settings.get("theme")["style"]
        except Exception as e:
            color = "Silver"
            style = "Dark"
        self.theme_cls.primary_palette = color
        self.theme_cls.theme_style = style
        self.ui = Builder.load_file("./ui/update.kv")
        self.ui.transition = FadeTransition()
        self.title = "YouTubeXstream"
        return self.ui

        # try:
        #     os.execv(sys.executable,["python","main.py", "Failed_Update", f"{index}"])
        # except Exception as e:
        #     index = datetime.today()
        #     error = f"[b][color=#fa0000][ {index}@updater ]:[/color][/b]\n(\n\n{e}\n\n)\n"
        #     try:
        #         with open("crashdump.txt","a") as file:
        #             file.write(error)
        #     except:
        #         with open("crashdump.txt","w") as file:
        #             file.write(error)        

if __name__ == "__main__":
    try:
        UpdateApp().run()
    
    except Exception as e:
        index = datetime.today()
        error = f"[b][color=#fa0000][ {index}@updater ]:[/color][/b]\n(\n\n{e}\n\n)\n"
        try:
            with open("crashdump.txt","a") as file:
                file.write(error)
        except:
            with open("crashdump.txt","w") as file:
                file.write(error)
        try:
            os.execv(sys.executable,["python","main.py", "Failed_Update", f"\"{index}\""])
        except Exception as e:
            index = datetime.today()
            error = f"[b][color=#fa0000][ {index}@updater ]:[/color][/b]\n(\n\n{e}\n\n)\n"
            try:
                with open("crashdump.txt","a") as file:
                    file.write(error)
            except:
                with open("crashdump.txt","w") as file:
                    file.write(error)