import json
import os
os.environ["KIVY_VIDEO"] = "ffpyplayer"
os.environ["KCFG_KIVY_WINDOW_ICON"] = "./data/logo.ico"
# os.environ["KCFG_KIVY_LOG_ENABLE"] = "0"
# os.environ["KIVY_NO_CONSOLELOG"] = "1"
from dotenv import load_dotenv
load_dotenv()
import sys
from kivy.resources import resource_add_path, resource_find

resource_add_path(os.path.join("."))
resource_add_path(os.path.join("./data"))
from kivy.config import Config
# Config.set("log_enable")
Config.set('kivy', 'window_icon', resource_find("logo.ico"))
Config.write()

from kivymd.icon_definitions import md_icons
from difflib import SequenceMatcher
import socket
from kivy.network.urlrequest import UrlRequest
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.menu import MDDropdownMenu
from data.data import themes
from kivymd.uix.filemanager import MDFileManager
from datetime import datetime
import re
import subprocess
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar,MDSnackbarText,MDSnackbarSupportingText,MDSnackbarButtonContainer,MDSnackbarCloseButton
from kivymd.uix.recycleview import MDRecycleView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton,MDButtonText,MDButtonIcon
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogIcon,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
    MDDialogContentContainer,
)
from kivymd.uix.divider import MDDivider

from kivy.utils import format_bytes_to_human
from kivy.lang import Builder
from pytube import YouTube
from kivy.clock import Clock,mainthread
from kivy.properties import StringProperty,NumericProperty,ObjectProperty,DictProperty,BooleanProperty
from threading import Thread
from kivy.utils import QueryDict,platform,get_hex_from_color
from queue import Queue
from pyyoutube import Api
from controllers.videoplayer import VideoPlayerX
from datetime import datetime
videos_dir = ""
if platform == "win":
    videos_dir = os.path.join(os.environ.get("USERPROFILE"),"Videos")
elif platform == "macosx":
    videos_dir = os.path.join(os.environ.get("HOME"),"Movies")
else:
    videos_dir = os.path.join(os.environ.get("HOME"),"Videos")

import subprocess

def merge_image_with_audio(image_path, audio_path, output_path):
    command = [
        'ffmpeg',
        '-loop', '1',
        '-i', image_path,
        '-i', audio_path,
        '-c:v', 'libx264',
        '-c:a', 'copy',
        '-shortest',
        output_path
    ]
    subprocess.run(command)

class VideoCard(MDBoxLayout):
    image_link = StringProperty("")
    video_link = StringProperty("")
    title = StringProperty("")
    desc = StringProperty("")
    channel = StringProperty("")
    publishedAt = StringProperty("")

class MDVideoPlayer(VideoPlayerX):
    pass

class SearchResults(MDRecycleView):
    pass


class YouTubeApp(MDApp):
    path = StringProperty("")
    VIDS_PATH = os.path.join(videos_dir,"YoutubeX")
    queue = None
    background_tasks = None
    jobs = NumericProperty()
    stream = ObjectProperty()
    is_online = BooleanProperty()
    api = None
    crash_text = ""
    try:
        store = JsonStore("user_settings.json") 
        date = datetime.today().date()
        api_key = store.get("user_credentials")["api_key"]
        search_disabled = False
        try:
            rem_searches = store.get("search")[f"{date}"]
        except Exception as e:
            store.put("search",**{f"{date}":50})
            rem_searches = store.get("search")[f"{date}"]
    except:
        api_key =""
        rem_searches = 0
        search_disabled = True
    if not search_disabled:        
        try:
            api = Api(api_key=api_key)
        except:
            search_disabled = True
    api_key = StringProperty(api_key)
    rem_searches = NumericProperty(rem_searches)
    def get_crash_text(self):
        crashdump_path = resource_find("crashdump.txt")
        no_crash = "[b][color=#00fa00]No crash so far[/color][/b]"
        try:
            if crashdump_path:
                with open(crashdump_path,"r") as file:
                    text = file.read()
                    if text == "":
                        return no_crash
                    else:
                        return text
            else:
                return no_crash
        except:
            return no_crash

    def on_api_key(self,instance,value):
        try:
            self.api = Api(api_key=value)
            self.search_disabled = False
        except:
            self.search_disabled = True
    def on_rem_searches(self,instance,value):
        try:
            self.store.put("search",**{f"{self.date}":value})
        except Exception as e:
            pass
    def check_for_updates(self):
        req = UrlRequest("https://api.github.com/repos/bxw-855/YouTubeXStream/releases/latest",
                         on_success=self.is_update,
                         req_headers = {"User-Agent":"YouTubeXStream"}
                         )

    def is_update(self,request,online_release):
        def _version_weight(tag_name):
            version = tag_name[1:].split(".")
            return int(version[0])*100+int(version[1])*10+int(version[2])
        def get_my_release():
            try:
                with open(resource_find("release.json"),"r") as file:
                    return json.loads(file.read())
            except:
                self.show_toast("Missing","Could not find release.json\nRecommend reinstalling app to inorder get updates")
                return None
        my_release = get_my_release()
        if my_release:
            try:
                if _version_weight(online_release["tag_name"]) > _version_weight(my_release["tag_name"]):
                    self.update_dialog({"version":online_release["tag_name"]})
            except Exception as e:
                self.show_toast("Sth went wrong while checking for update",f"{e}\nRecommend reinstalling app to inorder get updates")
                return None            

    def update_dialog(self,data):
            MDDialog(
                # ----------------------------Icon-----------------------------
                MDDialogIcon(
                    icon="update",
                ),
                # -----------------------Headline text-------------------------
                MDDialogHeadlineText(
                    text="Would you like to update to the latest version?",
                ),
                # -----------------------Supporting text-----------------------
                MDDialogSupportingText(
                    text=f"This will close the app and launch the updater and then update the app to version {data["version"]}",
                ),
                # -----------------------Custom content------------------------
                # MDDialogContentContainer(
                #     MDDivider(),
                    
                #     MDDivider(),
                #     orientation="vertical",
                # ),
                # ---------------------Button container------------------------
                MDDialogButtonContainer(
                    MDButton(
                        MDButtonText(text="No Thanks"),
                        style="text",
                        on_press = lambda instance,*_: instance.parent.parent.parent.parent.dismiss()
                    ),
                    MDButton(
                        MDButtonText(text="Yes Please"),
                        style="text",
                        on_press = self.update_app

                    ),
                    spacing="8dp",
                ),
                auto_dismiss = False
                # -------------------------------------------------------------
            ).open()
    def update_app(self,*_):
        self.stop()         
        try:
            os.execv(sys.executable,["python","updater.py"])
        except Exception as e:
            index = datetime.today()
            error = f"[b][color=#fa0000][ {index} ]:[/color][/b]\n(\n\n{e}\n\n)\n"
            try:
                self.show_toast("Failed update",f"{e}")
                with open("crashdump.txt","a") as file:
                    file.write(error)
            except:
                with open("crashdump.txt","w") as file:
                    file.write(error)

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
            self.screen.ids.status_bar.md_bg_color = self.theme_cls.secondaryContainerColor

        else:
            error_color = get_hex_from_color(self.theme_cls.errorColor)
            self.screen.ids.status_bar.md_bg_color = self.theme_cls.errorContainerColor
            self.screen.ids.video_title.text = f"[b][color={error_color}]You are offline[/color][/b]"
            self.show_toast("Ofline","You are offline, connect back to download and search\nbut you can still watch downloaded in downloads page  :(")

    def worker(self,queue):
        while True:
            job = queue.get() 
            job()
            queue.task_done()
    def bg_worker(self,queue):
        while True:
            job = queue.get() 
            job()
            queue.task_done()
    def add_bg_task(self,task):
        self.background_tasks.put(task)
        
    @mainthread
    def on_download_progress(self,chunk,file_handler,bytes_rem):
        filesize = self.stream.filesize
        downloaded = (filesize-bytes_rem)
        self.screen.ids.job_progress_label.text = f"{format_bytes_to_human(downloaded)}/{format_bytes_to_human(filesize)}" 
        percentage_completion  = (downloaded/filesize)*100
        self.screen.ids.job_progress.value = percentage_completion


    @mainthread
    def on_download_complete(self,stream,file_path,audio):
        def _completed_audio(file_path):
            try:
                self.show_toast("Audio Processing","trying to convert to audio :)")
                new_filename = "A" + os.path.basename(file_path)
                new_path = os.path.join(self.VIDS_PATH,new_filename)
                merge_image_with_audio(resource_find("video_preview.jpeg"), file_path, new_path)
                os.remove(file_path)
                file_path = new_path
            except Exception as e:
                self.show_toast("Failure",f"{e}\nBut original exists at {file_path}")
            self.reset_prev()
            self.show_toast(title=f"Success: Download and processing Completed",details=f"At {file_path}")
            if self.screen.ids.vid_player.source == ""  and not os.path.exists(self.screen.ids.vid_player.source) :
               self.screen.ids.vid_player.source = file_path 
        def _completed_video(file_path):
            self.reset_prev()
            self.show_toast(title=f"Success: Download Completed",details=f"At {file_path}")
            if self.screen.ids.vid_player.source == ""  and not os.path.exists(self.screen.ids.vid_player.source) :
               self.screen.ids.vid_player.source = file_path 
        if audio:
            self.queue.put(lambda:_completed_audio(file_path))
        else:
            Clock.schedule_once(lambda _:_completed_video(file_path))

    @mainthread
    def on_stream(self,*args):
        def _download_started(dt):
            self.show_toast("New Download started",f"Downloading {self.stream.title}")
        Clock.schedule_once(_download_started)            

    def download_video(self,link,audio):
        if self.is_online:
            try:
                self.screen.ids.job_progress_label.text = "starting..."
                yt = YouTube(link,on_progress_callback=self.on_download_progress,on_complete_callback=lambda *args:self.on_download_complete(*args,audio))
                if audio:
                    streams = yt.streams.filter(only_audio=True,file_extension="mp4") 
                    prefix= ""
                else:
                    streams = yt.streams.filter(progressive=True,file_extension="mp4") 
                    prefix= "V"
                    
                self.stream = streams[-1]
                if self.stream:
                    filesize = format_bytes_to_human(self.stream.filesize)
                    self.screen.ids.job_progress_label.text = f"{0}/{filesize}" 
                    self.screen.ids.video_title.text = self.stream.title
                    self.stream.download(output_path=self.VIDS_PATH,filename_prefix=f"{prefix}_{yt.author}_")
                else:
                    self.show_toast("Missing",f"Could not find video or audi matching {link}\ntry downloading another format")
            except Exception as e:
                self.show_toast("Download Failure",f"Cause: {e}")
                self.reset_prev()
        else:
            self.show_toast("Offline","Connect to the interneet to download videos\nbut you can still watch downloaded videos")
    @mainthread
    def reset_prev(self):
        self.screen.ids.job_progress_label.text = ""
        self.screen.ids.video_title.text = "Try downloading multiple"
        self.screen.ids.job_progress.value = 0
        self.jobs -= 1
        self.screen.ids.active_jobs.text = f"Jobs: {self.jobs}"
    
    def on_start(self):
        super().on_start()
        # for user activities
        self.queue = Queue()
        worker_thread = Thread(target=self.worker,args=(self.queue,))
        worker_thread.daemon = True
        worker_thread.start()

        # for bg activites
        self.background_tasks = Queue()
        bg_worker_thread = Thread(target=self.bg_worker,args=(self.background_tasks,))
        bg_worker_thread.daemon = True
        bg_worker_thread.start()
        self.is_online = self.isOnline()
        if self.is_online:
            self.search_for_video(self.startup_search)
            if len(sys.argv) > 1:
                arg1 = sys.argv[1]
                arg2 = sys.argv[2]
                if arg1 == "Failed_Update":
                    self.show_toast("Failed Update",f"Check crush dump entry:\n[ {arg2}@updater ]\n for details")
                else:
                    self.add_bg_task(self.check_for_updates)        
            else:
                self.add_bg_task(self.check_for_updates)        

        Clock.schedule_interval(self._isOnline,5)
    def on_jobs(self,*args):
        if self.jobs == 0:
            pass

    def search_for_video(self,query):
        def _search():
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
                elif not self.search_disabled and self.rem_searches>0:    
                    results = self.api.search(q=query,count=10).items
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
                    self.rem_searches -= 1
                    self.show_toast("Search",f"You are now remaining with {self.rem_searches} searches of your daily quota")
                else:
                    self.show_toast("Search",f"You haven`t configured a youtube api key in settings, for search to be enabled\nbut you can still paste links of videos in the search box to download youtube video of specified link\n or you reached your quota")
                    
            except Exception as e:
                self.show_toast("failed to search",f"Reason: {e}")
                Clock.schedule_once(lambda x:self.show_toast("Search Tokens Depleted","You probably run out off search tokens\nbut you can still paste video links to download videos"),5)
        if self.is_online:
            self.add_bg_task(_search)
        else:
            self.show_toast("Offline","connect to the internet to download and search videos")

    def build(self): 
        
        self.user_settings = JsonStore("user_settings.json")
        if not os.path.exists(self.VIDS_PATH):
            os.mkdir(self.VIDS_PATH)
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
        self.crash_text = self.get_crash_text()
        self.theme_cls.primary_palette = color
        self.theme_cls.theme_style = style
        self.screen = Builder.load_file("./ui/main.kv")
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
                duration = 5,
                y="10dp",
                pos_hint = {"right":0.99},
                size_hint_x = .4,
                padding="5dp",
                orientation="horizontal"
            ).open()
        Clock.schedule_once(_show)
    @mainthread
    def _stream(self,video,stream):
        self.screen.sm.current ="video_screen"
        self.screen.ids.vid_player.source = stream.url
        self.screen.ids.vid_player.video_title.text = video   
        self.screen.ids.vid_player.state = "play"     
    def stream_video(self,video,link):
        if self.is_online:
            try:
                
                yt = YouTube(link,on_complete_callback=None,on_progress_callback=None)
                streams = yt.streams.filter(progressive=True,file_extension="mp4") #res [720p,480p,360p,240p,144p]
                stream = streams[-1]
                if stream:
                    self.show_toast("Streaming",f"Now streaming {video}\nto watch it later and while offline download it")
                    self._stream(video,stream)
            except Exception as e:
                self.show_toast("Stream Failure",f"Cause: {e}")
        
    def show_video(self,video:str,link,*args):
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
        @mainthread
        def _update(path,video):        
            self.screen.sm.current = "video_screen"
            self.screen.ids.vid_player.source = path
            self.screen.ids.vid_player.video_title.text = video
            self.screen.ids.vid_player.state = "play"            
        def _show():
            paths = os.listdir(self.VIDS_PATH)

            path = [(path,similar(video,path)) for path in paths if similar(video,path)>0.5]

            if path:
                path = max(path,key=lambda x: x[1])
                path= os.path.join(self.VIDS_PATH,path[0])
                _update(path,video)
            else:
                self.stream_video(video,link)
        if os.path.exists(self.VIDS_PATH):
            self.add_bg_task(_show)
    
    def open_video_link(self,video_link,*args):
        def _open():
            try:
                result = subprocess.run(["start",video_link],shell=True,stdout=subprocess.PIPE)
                if result.returncode == 0:
                    self.show_toast("success",f"opened: {video_link}")
                else:
                    self.show_toast("Failed",f"Could not open this link in browser {video_link}")
            except Exception as e:
                self.show_toast("Failed",f"{e}")
        self.add_bg_task(_open)

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
        self.screen.ids.vid_player.video_title.text = os.path.basename(path)
        
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
        elif name=="download_type":
            menu_items = [
                {
                    "text": f"{download_type}",
                    "on_release": lambda x=download_type: self.download_type_menu_callback(item,x),
                } for download_type in ["Video","Audio Only"]
            ]
        MDDropdownMenu(caller=item, items=menu_items).open()

    def download_type_menu_callback(self,instance,download_type):
        link = instance.video_link
        author = instance.video_channel
        title = instance.video_title
        if download_type == "Video":
            audio = False
        else:
            audio = True
        def _add(dt):
            job = lambda audio=audio,link=link: self.download_video(link,audio)
            self.queue.put(job)
            self.jobs += 1 
            self.screen.ids.active_jobs.text = f"Jobs: {self.jobs}"
            self.show_toast("Success: New job added",f"{title}\nby @{author}")
        Clock.schedule_once(_add)
            
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
    def update_api_key(self,instance,*_):
        try:
            self.user_settings.put("user_credentials",api_key=instance.text)
            self.api_key = instance.text
            self.api = Api(api_key=self.api_key)
            self.search_disabled = False
        except Exception as e:
            self.search_disabled = True
            self.show_toast("Failed Settings Update",f"{e}")

if __name__ == '__main__':
    try:
        if hasattr(sys, '_MEIPASS'):
            resource_add_path(os.path.join(sys._MEIPASS))
        YouTubeApp().run()
    except Exception as e:
        index = datetime.today()
        error = f"[b][color=#fa0000][ {index}@main ]:[/color][/b]\n(\n\n{e}\n\n)\n"
        try:
            with open("crashdump.txt","a") as file:
                file.write(error)
        except:
            with open("crashdump.txt","w") as file:
                file.write(error)
