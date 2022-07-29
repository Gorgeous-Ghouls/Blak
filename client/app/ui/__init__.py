from datetime import datetime

from kivy import Logger
from kivy.core.window import Window
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.button import BaseButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.list import OneLineListItem
from kivymd.uix.screen import MDScreen

from ..utils import Colors


class Dialog(MDDialog):
    """Custom dialog with a few changes"""

    active = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        if title := kwargs.get("title", None):
            kwargs["title"] = f"[color={Colors.accent_bg_text.value}]{title}[/color]"

        super().__init__(**kwargs)

    def on_active(self, instance, active):
        """Closes dialog if active set to False"""
        if not active:
            self.dismiss()


class LoginScreen(MDFloatLayout):
    """Login Screen for the app"""

    def reset_fields(self):
        """Reset the username and password field."""
        self.ids["username"].text = ""
        self.ids["password"].text = ""


class ChatItem(MDCard):
    """Class representing a chat."""

    # ask can I use dataclass here somehow ? the args in __init__ need to be set before super call

    def __init__(
        self,
        username: str,
        custom_id: str,
        last_seen: str = "",
        msg_count: str = "",
        **kwargs,
    ):

        self.username = username
        self.custom_id = custom_id
        self.last_seen = last_seen
        self.msg_count = msg_count
        super(ChatItem, self).__init__()

    def on_touch_down(self, touch) -> bool:
        """Event Fired everytime mouse is released to tap is released."""
        if self.collide_point(*touch.pos):
            screen_manager: ScreenManager
            screen_manager = MDApp.get_running_app().root.ids["chats_screen_manager"]
            if screen_manager.has_screen(self.custom_id):
                screen_manager.current = self.custom_id
                return True
            else:
                Logger.info(f"{self.custom_id} screen not found")
            return False

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


class OneLineListItemAligned(OneLineListItem):
    """OneLineListItem that allows horizontal alignment"""

    def __init__(self, halign, **kwargs):
        super(OneLineListItemAligned, self).__init__(**kwargs)
        self.ids._lbl_primary.halign = halign
        if halign == "right":
            self.md_bg_color = Colors.get_kivy_color("primary_bg_text")


class ChatMessagesScreen(MDScreen):
    """Class representing a chat screen."""

    disable_chat_input: BooleanProperty(False)

    def __init__(self, other_user: str, **kwargs):
        self.other_user = other_user
        super(ChatMessagesScreen, self).__init__(**kwargs)
        from ..lib.kivy_manager import ClientUI

        self.app: ClientUI = MDApp.get_running_app()
        self.times_validated = 0

    def send_message(self, message: str):
        """Send message to server."""
        if message:
            msg_data = {
                "type": "msg.send",
                "other_id": self.other_user,
                "data": message,
                "timestamp": str(datetime.now().timestamp()),
                "room_id": self.name,
            }
            self.disable_chat_input = True
            self.app.send_data(value=msg_data)

    def add_message(
        self,
        message: str,
        text_color: list,
        halign: str = "left",
        clear_input: bool = False,
    ) -> OneLineListItemAligned:
        """Adds a received message to the screen."""
        if clear_input:
            message = self.ids["chat_input"].text
            self.ids["chat_input"].text = ""

        chat_message = OneLineListItemAligned(
            halign, text=message, theme_text_color="Custom", text_color=text_color
        )
        self.ids["chat_list"].add_widget(chat_message)
        return chat_message

    def scroll_to_message(self, widget: OneLineListItemAligned):
        """Scrolls the messages view to the specified message"""
        list_scroll_view: ScrollView
        list_scroll_view = self.ids["list_scroll_view"]
        list_scroll_view.scroll_to(widget)

    def on_disable_chat_input(self, instance, value):
        """Fired every time disable_chat_input changes value"""
        if value:
            self.ids["chat_input"].disabled = True
        else:
            self.ids["chat_input"].disabled = True


class NewChatInputFields(MDGridLayout):
    """Fields for when adding a new chat"""

    pass
