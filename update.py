from kivymd.app import MDApp
from kivy.network import urlrequest
from kivy.clock import Clock
from kivy.lang import Builder


class UpdateApp(MDApp):
    def get_latest():
        print("ppp")
    def on_start(self):
        super().on_start()
        self.user_data_path = self._get_user_data_dir()

    def build(self):
        self.ui = Builder.load_file("update.kv")
        self.title = "YoutubeXstream"
        return self.ui

if __name__ == "__main__":
    UpdateApp().run()