import os
os.environ["KIVY_VIDEO"] = "ffpyplayer"
# os.environ["KIVY_NO_CONSOLELOG"] = "1"
from kivy.config import Config
# Config.set("log_enable")
from difflib import SequenceMatcher
import socket
from kivy.network.urlrequest import UrlRequest
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.videoplayer import VideoPlayer
from data import themes
from kivymd.uix.filemanager import MDFileManager
from datetime import datetime
import re
import subprocess
from kivymd.app import MDApp
from kivymd.uix.snackbar import MDSnackbar,MDSnackbarText,MDSnackbarSupportingText,MDSnackbarButtonContainer,MDSnackbarCloseButton
from kivymd.uix.recycleview import MDRecycleView
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.utils import format_bytes_to_human
from kivy.lang import Builder
from pytube import YouTube
from kivy.clock import Clock,mainthread
from kivy.properties import StringProperty,NumericProperty,ObjectProperty,DictProperty,BooleanProperty
from threading import Thread
from kivy.utils import QueryDict,platform
from queue import Queue
from pyyoutube import Api
import random
import tempfile 

# get default videos dir

videos_dir = ""
if platform == "Windows":
    videos_dir = os.path.join(os.environ.get("USERPROFILE"),"Videos")
elif platform == "Darwin":
    videos_dir = os.path.join(os.environ.get("HOME"),"Movies")
else:
    videos_dir = os.path.join(os.environ.get("HOME"),"Videos")

temp_dir = tempfile.TemporaryDirectory(delete=False)

keys = [
    "AIzaSyBygR7Oz_pQNayCVYLQKSmqyOpNcds11vk",
    "AIzaSyBWiY9WwBV2u9lMXrnM-MlaLAezXHcl3WU",
    "AIzaSyBWw2I3hiagIv9GaGBwLGKCr846ZSUQcCE",
    "AIzaSyBlAPfHX22YO0Mh-svQky93vBwzhTdNEHU",
    "AIzaSyCdhIfZoXfxU5yFCZrHgwNEUZHQE8dJmVg"
]    
api = Api(api_key=random.choice(keys))

def check_for_updates():
    #req = UrlRequest(url, on_success, on_redirect, on_failure, on_error,
                    # on_progress, req_body, req_headers, chunk_size,
                    # timeout, method, decode, debug, file_path, ca_file,
                    # verify)
    req = UrlRequest("htttps://")

class VideoCard(MDBoxLayout):
    image_link = StringProperty("")
    video_link = StringProperty("")
    title = StringProperty("")
    desc = StringProperty("")
    channel = StringProperty("")
    publishedAt = StringProperty("")

class VideoPlayerCustom(VideoPlayer):
    VIDS_PATH = os.path.join(videos_dir,"YoutubeX")
    def _do_video_load(self,*largs):
        super()._do_video_load(*largs)
        self._video.bind(eos=self.next_video)
        
    def next_video(self,instance,*args):
        app = MDApp.get_running_app()
        try:
            user_settings = JsonStore("user_settings.json")
            next_video = user_settings.get("Video Preferences")["Auto_Next"] 
        except Exception as e:
            print(e)
            next_video = True
        def _show(dt):

            paths = [os.path.join(self.VIDS_PATH,video) for video in os.listdir(self.VIDS_PATH) if ".mp4" in video]
            source = self.source
            if source and next_video == True:
                current_i = paths.index(source)
                if current_i > -1 and current_i < (len(paths)-1):
                    path = paths[(current_i+1)]
                else:
                    path = paths[0]
                if path:
                    # path= os.path.join(self.VIDS_PATH,path)
                    self.source = path
                    self.state = "play"
        if os.path.exists(self.VIDS_PATH):
            Clock.schedule_once(_show)

class SearchResults(MDRecycleView):
    pass

class UpdateDialog():
    pass
class YouTubeApp(MDApp):
    path = StringProperty("")
    VIDS_PATH = os.path.join(videos_dir,"YoutubeX")
    queue = None
    jobs = NumericProperty()
    stream = ObjectProperty()
    api = None
    is_online = BooleanProperty()
    def _isOnline(self,dt):
        self.is_online = self.isOnline()
    def isOnline(self):
        try:
            sock = socket.create_connection(("www.google.com",80))
            if sock != None:
                sock.close()
                return True
        except:
            return False
    def on_is_online(self,app,online):
        if online:
            self.show_toast("Online","You are back online, you can now search and download :)")
            self.screen.ids.video_title.text ="You can now search and download"     
        else:
            self.screen.ids.video_title.text = "[color=#ff0000]You are offline[/color][color=#00ff00]but can still watch downloads[/color]"
            self.show_toast("Ofline","You are offline, connect back to download and search\nbut you can still watch downloaded in downloads page  :(")

    def worker(self,queue):
        while True:
            job = queue.get() # expects (link,quality)
            self.download_video(*job)
            queue.task_done()
    @mainthread
    def on_download_progress(self,chunk,file_handler,bytes_rem):
        filesize = self.stream.filesize
        downloaded = (filesize-bytes_rem)
        self.screen.ids.job_progress_label.text = f"{format_bytes_to_human(downloaded)}/{format_bytes_to_human(filesize)}" 
        percentage_completion  = (downloaded/filesize)*100
        self.screen.ids.job_progress.value = percentage_completion


    @mainthread
    def on_download_complete(self,stream,file_path):
        def _completed(dt):
            self.reset_prev()
            self.show_toast(title=f"Success: Download Completed",details=f"At {file_path}")
            if self.screen.ids.vid_player.source == ""  and not os.path.exists(self.screen.ids.vid_player.source) :
               self.screen.ids.vid_player.source = file_path 
        Clock.schedule_once(_completed)

    @mainthread
    def on_stream(self,*args):
        def _download_started(dt):
            self.show_toast("New Download started",f"Downloading {self.stream.title}")
        Clock.schedule_once(_download_started)            

    def download_video(self,link,title):
        if self.is_online:
            try:
                self.screen.ids.job_progress_label.text = "starting..."
                yt = YouTube(link,on_progress_callback=self.on_download_progress,on_complete_callback=self.on_download_complete)
                streams = yt.streams.filter(progressive=True,file_extension="mp4") #res [720p,480p,360p,240p,144p]
                self.stream = streams[-1]
                if self.stream:
                    filesize = format_bytes_to_human(self.stream.filesize)
                    self.screen.ids.job_progress_label.text = f"{0}/{filesize}" 
                    self.screen.ids.video_title.text = self.stream.title
                    self.stream.download(output_path=self.VIDS_PATH,filename_prefix=f"{self.stream.resolution}_{yt.author}_")
            except Exception as e:
                if self.stream:
                    self.show_toast("Download Failure",f"Cause: {e}")
                self.reset_prev()
        else:
            self.show_toast("Offline","Connect to the interneet to download videos\nbut you can still watch downloads")
    @mainthread
    def reset_prev(self):
        self.screen.ids.job_progress_label.text = ""
        self.screen.ids.video_title.text = "Try downloading multiple"
        self.screen.ids.job_progress.value = 0
        self.jobs -= 1
        self.screen.ids.active_jobs.text = f"Jobs: {self.jobs}"

    def on_start(self):
        super().on_start()
        self.queue = Queue()
        worker_thread = Thread(target=self.worker,args=(self.queue,))
        worker_thread.daemon = True
        worker_thread.start()
        Clock.schedule_interval(self._isOnline,5)
        self.is_online = self.isOnline()
        if not self.is_online:
            self.screen.ids.video_title.text = "[color=#ff0000]You are offline but you can still watch downloads[/color]"
            self.show_toast("Offline","Connect to the internet to search and download videos")
            
    def on_jobs(self,*args):
        if self.jobs == 0:
            pass

    def search_for_video(self,query):
        def _search(dt):
            self.screen.ids.rv.data = []
            regex_pattern = r"^(https?:\/\/)?([\w\-]+(\.[\w\-]+)+)(:[0-9]+)?(\/[\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?$"
            try:
                if re.match(regex_pattern,query):
                    yt = YouTube(query)                    
                    data = {
                    "title": yt.title,
                    "desc": f"{yt.description}",
                    "image_link": f"{yt.thumbnail_url}",
                    "video_link": query,
                    "channel": yt.author,
                    "publishedAt": f"{yt.publish_date}"
                    } 
                    self.screen.ids.rv.data.append(data)
                else:    
                    results = api.search(q=query,count=10).items
                    matches = [QueryDict(result.to_dict()) for result in results]
                    if matches:
                        for match in matches:
                            published_at = match.snippet["publishedAt"]
                            date_obj = datetime.strptime(published_at,"%Y-%m-%dT%H:%M:%SZ")
                            published_at = date_obj.strftime("%b %d, %Y")
                            data = {
                            "title": match.snippet["title"],
                            "desc": match.snippet["description"],
                            "image_link": match.snippet["thumbnails"]["high"]["url"],
                            "video_link": f"https://youtube.com/watch?v={match.id["videoId"]}",
                            "channel": match.snippet["channelTitle"],
                            "publishedAt": published_at
                            } 
                            self.screen.ids.rv.data.append(data)
                    else:
                        self.show_toast("No result",f"Nothing has been found matching your query of\n{query}")
            except Exception as e:
                self.show_toast("failed to search",f"Reason: {e}")
                Clock.schedule_once(lambda x:self.show_toast("Search Tokens Depleted","You probably run out off search tokens\nbut you can still paste video links to download videos"),2)
        if self.is_online:
            Clock.schedule_once(_search,-1)
        else:
            self.show_toast("Offline","connect to the internet to download and search videos")

    def build(self): 
        self.user_settings = JsonStore("user_settings.json")

        try:
            color = self.user_settings.get("theme")["color"]
            style = self.user_settings.get("theme")["style"]
            self.startup_search = self.user_settings.get("startup")["query"]            
            self._next_video = self.user_settings.get("Video Preferences")["Auto_Next"]            
        except Exception as e:
            color = "Silver"
            style = "Dark"
            self.startup_search = "Anime Trailers" 
            self._next_video = True
        self.theme_cls.primary_palette = color
        self.theme_cls.theme_style = style
        self.search_for_video(self.startup_search)
        self.screen = Builder.load_file("./main.kv")
        self.title = "YouTubeXStream"
        return self.screen

    @mainthread
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

    def show_video(self,video:str,*args):
        # depracated
        def string_similarity(str1, str2):
            lcs_len = 0
            for i in range(len(str1)):
                for j in range(len(str2)):
                    if str1[i] == str2[j]:
                        curr_lcs = 1 + lcs_len if i > 0 and j > 0 and str1[i - 1] == str2[j - 1] else 1
                        lcs_len = max(lcs_len, curr_lcs)

            similarity = (lcs_len / max(len(str1), len(str2)))
            return similarity

        def similar(a, b):
            return SequenceMatcher(None, a, b).ratio()
        
        def _show(dt):
            paths = os.listdir(self.VIDS_PATH)

            path = [(path,similar(video,path)) for path in paths if similar(video,path)>0.7]

            if path:
                path = max(path,key=lambda x: x[1])
                path= os.path.join(self.VIDS_PATH,path[0])
                self.screen.sm.current = "video_screen"
                self.screen.ids.vid_player.source = path
                self.screen.ids.vid_player.state = "play"
            else:
                self.screen.sm.current = "video_screen"
                self.show_toast("Not found","video has not been found.Try downloading it")
        if os.path.exists(self.VIDS_PATH):
            Clock.schedule_once(_show)
    
    def open_video_link(self,video_link,*args):
        def _open(dt):
            try:
                result = subprocess.run(["start",video_link],shell=True,stdout=subprocess.PIPE)
                if result.returncode == 0:
                    self.show_toast("success",f"opened: {video_link}")
                else:
                    self.show_toast("Failed",f"Could not open this link in browser {video_link}")
            except Exception as e:
                self.show_toast("Failed",f"{e}")
        Clock.schedule_once(_open)

    def add_download_video_job(self,link,title,author,*args):
        def _add(dt):
            self.queue.put((link,title))
            self.jobs += 1 
            self.screen.ids.active_jobs.text = f"Jobs: {self.jobs}"
            self.show_toast("Success: New job added",f"{title}\nby @{author}")
        Clock.schedule_once(_add)

    def show_vids_folder(self):
            try:
                if os.path.exists(self.VIDS_PATH):
                    path = os.path.expanduser(self.VIDS_PATH)  
                    self.file_manager = MDFileManager(
                    exit_manager=self.exit_manager,
                    ext=[".mp4"],
                    select_path=self.select_path,  
                    )
                    self.file_manager.show(path)
                else:
                    self.show_toast("No downloads","Try downloading videos first") 
            except Exception as e:
                self.show_toast("Sth went wrong",f"{e}")

    def exit_manager(self, v,*args):
        self.file_manager.close()

    def select_path(self,path,*args):
        self.screen.sm.current = "video_screen"
        self.screen.ids.vid_player.source = path
        self.screen.ids.nav_drawer.set_state("toggle")
        self.screen.ids.vid_player.state = "play"
        self.file_manager.close()

    def open_menu(self, item,name):
        if name=="themeColor":
            menu_items = [
                {
                    "text": f"{theme}",
                    "on_release": lambda x=theme: self.theme_color_menu_callback(x),
                } for theme in themes
            ]
        elif name=="themeStyle":
            menu_items = [
                {
                    "text": f"{theme}",
                    "on_release": lambda x=theme: self.theme_style_menu_callback(x),
                } for theme in ["Dark","Light"]
            ]
        MDDropdownMenu(caller=item, items=menu_items).open()

    def theme_color_menu_callback(self,color,*args):
        try:
            self.theme_cls.primary_palette = color
            self.user_settings.put("theme",style=self.theme_cls.theme_style,color=color)
        except Exception as e:
            self.show_toast("Failed Settings Update",f"{e}")
            
    def theme_style_menu_callback(self,style,*args):
        try:
            self.theme_cls.theme_style = style
            self.user_settings.put("theme",style=style,color=self.theme_cls.primary_palette)
        except Exception as e:
            self.show_toast("Failed Settings Update",f"{e}")
    def update_startup_search(self,instance,*_):
        try:
            self.user_settings.put("startup",query=instance.text)
        except Exception as e:
            self.show_toast("Failed Settings Update",f"{e}")
    def update_next_video(self,instance,*_):
        try:
            self.user_settings.put("Video Preferences",Auto_Next=instance.active)
        except Exception as e:
            self.show_toast("Failed Settings Update",f"{e}")

if __name__ == "__main__":
    YouTubeApp().run()



