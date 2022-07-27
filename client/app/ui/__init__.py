from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.button import BaseButton
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.screen import MDScreen

from ..utils import Colors


class ChatItem(MDCard):
    """Class representing a chat."""

    # ask can I use dataclass here somehow ? the args in __init__ need to be set before super call

    def __init__(
        self,
        username: str,
        custom_id: str,
        last_seen: str = "",
        msg_count: str = "",
        **kwargs
    ):

        self.username = username
        self.custom_id = custom_id
        self.last_seen = last_seen
        self.msg_count = msg_count
        super(ChatItem, self).__init__()

    def on_touch_up(self, touch):
        """Event Fired everytime mouse is released to tap is released."""
        if self.collide_point(*touch.pos):
            screen_manager: ScreenManager
            screen_manager = MDApp.get_running_app().root.ids["chats_screen_manager"]
            if screen_manager.has_screen(self.custom_id):
                screen_manager.current_screen = self.custom_id

            # switch screen to the chat


class TitleBar(MDFloatLayout):
    """Custom TitleBar for the app"""

    md_bg_color = get_color_from_hex(Colors.accent_bg.value)
    button_bg = get_color_from_hex(Colors.primary_bg.value)
    button_size = "15sp"

    def __init__(self, **kwargs):
        super(TitleBar, self).__init__(**kwargs)
        from ..lib.kivy_manager import ClientUI

        self.app: ClientUI = MDApp.get_running_app()

    @staticmethod
    def fix_layout():
        """Hotfix to make sure titlebar is shown correctly on win and mac"""
        Window.size = Window.size[0], Window.size[1] + 1

    def handle_buttons(self, instance: BaseButton):
        """Callback Function for all buttons in titlebar

        :param instance a button object that is a subclass of kivymd.uix.button.BaseButton

        A button object was chosen instead of say a string, so that later on the caller itself can be edited
        """
        match_string = None
        if hasattr(instance, "icon"):
            match_string = instance.icon

        if match_string:
            match match_string:
                case "close":
                    self.app.stop()
                case "window-minimize":
                    self.app.root_window.minimize()
                case "window-maximize":
                    self.app.root_window.maximize()


class ChatScreen(MDScreen):
    """Class representing a chat screen."""

    def __init__(self, **kwargs):
        super(ChatScreen, self).__init__(**kwargs)
        from ..lib.kivy_manager import ClientUI

        self.app: ClientUI = MDApp.get_running_app()

    def send_message(self):
        """Send message to server."""
        pass
