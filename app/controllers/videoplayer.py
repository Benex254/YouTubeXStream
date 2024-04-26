import os
from kivymd.app import MDApp
# from kivy.core.audio import SoundLoader

from kivy.uix.behaviors import FocusBehavior
from kivy.metrics import dp
from kivy.utils import platform
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.core.audio import SoundLoader
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.behaviors import HoverBehavior
from kivymd.uix.slider import MDSlider
from kivy.clock import Clock
from kivymd.uix.fitimage import FitImage
from kivy.core.video import Video as CoreVideo
from kivy.animation import Animation
from kivy.resources import resource_find,resource_add_path
from kivy.properties import (BooleanProperty, NumericProperty, ObjectProperty,
                             OptionProperty, StringProperty,ListProperty)

from kivy.lang import Builder


with open(
    os.path.join("ui","videoplayer.kv"), encoding="utf-8"
) as kv_file:
    Builder.load_string(kv_file.read())
# time.strftime()
videos_dir = ""
if platform == "win":
    videos_dir = os.path.join(os.environ.get("USERPROFILE"),"Videos")
elif platform == "macosx":
    videos_dir = os.path.join(os.environ.get("HOME"),"Movies")
else:
    videos_dir = os.path.join(os.environ.get("HOME"),"Videos")

resource_add_path(os.path.join("."))
resource_add_path(os.path.join("./data"))
class MDVideo(FitImage):
    _preview_path = resource_find("video_preview.jpeg")
    preview = StringProperty(_preview_path, allownone=True)
    state = OptionProperty('stop', options=('play', 'pause', 'stop'))
    play = BooleanProperty(False, deprecated=True)
    eos = BooleanProperty(False)
    loaded = BooleanProperty(False)
    position = NumericProperty(-1)
    duration = NumericProperty(-1)
    volume = NumericProperty(1.)
    options = ObjectProperty({})
    _video_load_event = None

    def __init__(self, **kwargs):
        self._video = None
        super(MDVideo, self).__init__(**kwargs)
        self.fbind('source', self._trigger_video_load)
        self.background_color = [0,0,0]
        if "eos" in kwargs:
            self.options["eos"] = kwargs["eos"]
        if self.source:
            self._trigger_video_load()

    def texture_update(self, *largs):
        if self.preview:
            self.set_texture_from_resource(self.preview)
        else:
            self.set_texture_from_resource(self.source)

    def seek(self, percent, precise=True):
        if self._video is None:
            raise Exception('Video not loaded.')
        self.state = "pause"
        self._video.seek(percent, precise=precise)
        self.state = "play"

    def _trigger_video_load(self, *largs):
        ev = self._video_load_event
        if ev is None:
            ev = self._video_load_event = Clock.schedule_once(
                self._do_video_load, -1)
        ev()

    def _do_video_load(self, *largs):
        if CoreVideo is None:
            return
        self.unload()
        if not self.source:
            self._video = None
            self.texture = None
        else:
            filename = self.source
            # Check if filename is not url
            if '://' not in filename:
                filename = resource_find(filename)
            self._video = CoreVideo(filename=filename, **self.options)
            self._video.volume = self.volume
            self._video.bind(on_load=self._on_load,
                             on_frame=self._on_video_frame,
                             on_eos=self._on_eos)
            if self.state == 'play' or self.play:
                self._video.play()
            self.duration = 1.
            self.position = 0.

    def on_play(self, instance, value):
        value = 'play' if value else 'stop'
        return self.on_state(instance, value)

    def on_state(self, instance, value):
        if not self._video:
            return
        if value == 'play':
            if self.eos:
                self._video.stop()
                self._video.position = 0.
            self.eos = False
            self._video.play()
        elif value == 'pause':
            self._video.pause()
        else:
            self._video.stop()
            self._video.position = 0

    def _on_video_frame(self, *largs):
        video = self._video
        if not video:
            return
        self.duration = video.duration
        self.position = video.position
        self.texture = video.texture
        self.canvas.ask_update()

    def _on_eos(self, *largs):
        if not self._video or self._video.eos != 'loop':
            self.state = 'stop'
            self.eos = True

    def _on_load(self, *largs):
        self.loaded = True
        self._on_video_frame(largs)

    def on_volume(self, instance, value):
        if self._video:
            self._video.volume = value

    def unload(self):
        '''Unload the video. The playback will be stopped.

        .. versionadded:: 1.8.0
        '''
        if self._video:
            self._video.stop()
            self._video.unload()
            self._video = None
        self.loaded = False

class MDVideoSlider(MDSlider):
    video = ObjectProperty(False)
    def on_touch_down(self,touch):
        super().on_touch_down(touch)        
        if self.collide_point(*touch.pos):
            self.video.seek(self.value)

class MediaControls(HoverBehavior,MDBoxLayout):
    show_transition = StringProperty("linear")

    show_duration = NumericProperty(0.2)
    
    hide_transition = StringProperty("linear")
    
    hide_duration = NumericProperty(0.2)
    

    def dismiss(self, *args) -> None:
        anim = Animation(
            opacity=0,
            height=0,
            t=self.hide_transition,
            d=self.hide_duration,
        )
        anim.start(self)

    def open(self) -> None:
        self._height = dp(100)
        anim = Animation(
            opacity=1,
            height=self._height,
            t=self.show_transition,
            d=self.show_duration,
        )
        
        anim.start(self)
   
    def on_enter(self,*args):
        self.open()
    def auto_close(self):
        def _auto_close(dt):
            if not self.hovering:
                self.dismiss()
        Clock.schedule_once(_auto_close,2)
    def on_leave(self,*args):
        self.dismiss()

class VideoPlayerX(FocusBehavior,MDFloatLayout):
    fullscreen = BooleanProperty(False)
    allow_fullscreen = BooleanProperty(True)
    videos_dir = StringProperty()
    current_video = NumericProperty(0)
    video_paths = ListProperty()
    video = ObjectProperty()
    video_title = ObjectProperty()
    media_controls = ObjectProperty()
    title = StringProperty("")
    source = StringProperty()
    state = StringProperty()
    
    # @coming soon
    def auto_hide_mouse(self):
        window = self.get_parent_window()
        def _hide(dt):
            window.show_cursor = False
        Clock.schedule_once(_hide,2)
    def on_source(self,instance,value):
        if ".mp3" in value:
            # self.video_ = SoundLoader.load(value)
            pass
            # self.video_.play()
        elif ".mp4" in value:
            self.video.source = value
        
    def on_videos_dir(self,app,value):
        if os.path.exists(value):
            self.video_paths = [filename for filename in os.listdir(value) if "mp4" in filename ]
            if self.video_paths:
                self.current_video = 0
                filename = self.video_paths[self.current_video]
                self.title = filename.split(".")[0]
                self.video.source = os.path.join(value,filename)          
    def on_current_video(self,app,value):
        dir = self.videos_dir
        if os.path.exists(dir):
            video_paths = [filename for filename in os.listdir(dir) if "mp4" in filename ]
            filename = video_paths[value]
            self.title = filename.split(".")[0]
            self.video.source = os.path.join(dir,filename)
            self.video.state = "play"
            self.ids.play_btn.icon ="pause"
    def on_state(self,instance,value):
        if value == "play":
            self.video.state = "play"
            self.ids.play_btn.icon ="pause"
        else:
            self.video.state = "pause"
            self.ids.play_btn.icon ="play"            
    def next_video(self):
        if self.videos_dir:
            video_paths = os.listdir(self.videos_dir)
            if self.current_video<(len(video_paths)-1):
                self.current_video +=1
            else:
                self.current_video = (len(video_paths)-1)

    def previous_video(self):
        if self.current_video>0:
            self.current_video -=1
        else:
            self.current_video = 0
    def on_touch_down(self, touch):
        if not self.media_controls.hovering:
            self.media_controls.open()
            self.media_controls.auto_close()
        if not self.collide_point(*touch.pos):
            return False
        if touch.is_double_tap and self.allow_fullscreen:
            self.fullscreen = not self.fullscreen
            return True
        return super(VideoPlayerX, self).on_touch_down(touch)
        
    def on_fullscreen(self, instance, value):
        window = self.get_parent_window()
        if not window:
            
            if value:
                self.fullscreen = False
                window.fullscreen = False
            return
        if not self.parent:
            if value:
                self.fullscreen = False
                window.fullscreen = False

            return

        if value:
            self._fullscreen_state = state = {
                'parent': self.parent,
                'pos': self.pos,
                'size': self.size,
                'pos_hint': self.pos_hint,
                'size_hint': self.size_hint,
                'window_children': window.children[:]}

            # remove all window children
            for child in window.children[:]:
                window.remove_widget(child)

            # put the video in fullscreen
            if state['parent'] is not window:
                window.fullscreen = True

                state['parent'].remove_widget(self)
            window.add_widget(self)

            # ensure the video widget is in 0, 0, and the size will be
            # readjusted
            self.pos = (0, 0)
            self.size = (100, 100)
            self.pos_hint = {}
            self.size_hint = (1, 1)

        else:
            state = self._fullscreen_state
            window.remove_widget(self)
            for child in state['window_children']:
                window.add_widget(child)
            self.pos_hint = state['pos_hint']
            self.size_hint = state['size_hint']
            self.pos = state['pos']
            self.size = state['size']
            window.fullscreen = False

            if state['parent'] is not window:
                state['parent'].add_widget(self)

    def show_playlist(self,instance):
        dir = self.videos_dir
        if os.path.exists(dir):
            filenames = [filename for filename in os.listdir(dir) if "mp4" in filename ] 
            if filenames:
                menu_items = [
                    {
                        "text": f"{filename}",
                        "on_release": lambda x=filename: self.show_playlist_callback(x),
                    } for filename in filenames
                ]
        MDDropdownMenu(caller=instance, items=menu_items).open()

    def show_playlist_callback(self,filename):
        dir = self.videos_dir
        try:
            filenames = [filename for filename in os.listdir(dir) if "mp4" in filename ] 
            self.current_video = filenames.index(filename)
        except:
            pass
class VideoApp(MDApp):
    def build(self):
        self.theme_cls.primary_pallete = "Pink"
        self.theme_cls.theme_style = "Dark"
        # self.ui = Builder.load_file("../ui/videoplayer.kv")
        ui = VideoPlayerX()
        return ui

if __name__ == "__main__":
    VideoApp().run()