from kivymd.app import MDApp
from kivy.network import urlrequest
from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.uix.snackbar import MDSnackbar,MDSnackbarText,MDSnackbarSupportingText,MDSnackbarButtonContainer,MDSnackbarCloseButton


class UpdateApp(MDApp):
    def get_latest():
        print("ppp")
    
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
    def on_start(self):
        super().on_start()
        self.user_data_path = self._get_user_data_dir()
        Clock.schedule_once(lambda x:self.show_toast("Search Tokens Depleted","You probably run out off search tokens\nbut you can still paste video links to download videos"),2)
    def build(self):
        self.ui = Builder.load_file("update.kv")
        self.title = "YouTubeXstream"
        return self.ui

if __name__ == "__main__":
    UpdateApp().run()