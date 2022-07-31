from __future__ import annotations

from datetime import datetime, timedelta

from kivy import Logger
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_hex_from_color
from kivymd.app import MDApp
from kivymd.uix.button import BaseButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.list import OneLineListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField

from ..utils import Colors


def days_hours_minutes_seconds(td: timedelta) -> tuple[int, int, int, int]:
    """Converts timedelta to days, hours, minutes, and secs

    :returns tuple(days, hours, minutes, secs)
    """
    return td.days, td.seconds // 3600, (td.seconds // 60) % 60, td.seconds


class Dialog(MDDialog):
    """Custom dialog with a few changes"""

    active = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        if title := kwargs.get("title", None):
            kwargs[
                "title"
            ] = f"[color={get_hex_from_color(Colors.accent_bg_text)}]{title}[/color]"
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


class ChatItem(MDGridLayout):
    """Class representing a chat."""

    # ask can I use dataclass here somehow ? the args in __init__ need to be set before super call

    Items: dict[str, ChatItem] = dict()
    username: str = StringProperty()
    custom_id: str = StringProperty()
    last_seen: str = StringProperty(defaultvalue="Never")
    msg_count: str = StringProperty(defaultvalue="0")

    def __init__(self, **kwargs):
        super(ChatItem, self).__init__(**kwargs)
        self.app = MDApp.get_running_app()
        self.timestamp: float = 0.0
        ChatItem.Items.update({self.custom_id: self})

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

    def set_last_seen(self, dt):
        """Updates last seen is called every second by a callback"""
        days, hours, minutes, secs = days_hours_minutes_seconds(
            datetime.now() - datetime.fromtimestamp(float(self.timestamp))
        )
        if days > 0:
            last_seen = f"{days}d"
        elif hours > 0:
            last_seen = f"{hours}h"
        elif minutes > 0:
            last_seen = f"{minutes}m"
        else:
            last_seen = f"{secs % 60}s"
        self.last_seen = f"{last_seen} ago"


class TitleBar(MDFloatLayout):
    """Custom TitleBar for the app"""

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

    def __init__(
        self,
        halign,
        message_id: str = None,
        timestamp: float | str = None,
        user_id: str = None,
        **kwargs,
    ):
        super(OneLineListItemAligned, self).__init__(**kwargs)
        self.user_id = user_id
        if message_id:
            self.message_id: str = message_id
        if timestamp:
            if isinstance(timestamp, str) and timestamp.isdigit():
                timestamp = float(timestamp)
            self.timestamp: float = timestamp
        else:
            self.timestamp = datetime.now().timestamp()

        self.ids._lbl_primary.halign = halign
        if halign == "right":
            self.md_bg_color = Colors.primary_bg_text


def get_focus(text_input_field: MDTextField):
    """Enable the focus on a MDTextField.

    :param text_input_field field to give focus to
    """

    def get_focus_wrapper(dt):
        text_input_field.focus = True

    Clock.schedule_once(get_focus_wrapper)


class ChatMessagesScreen(MDScreen):
    """Class representing a chat screen."""

    disable_chat_input: BooleanProperty(False)

    def __init__(self, other_user: str, **kwargs):
        self.other_user = other_user
        super(ChatMessagesScreen, self).__init__(**kwargs)
        from ..lib.kivy_manager import ClientUI

        self.app: ClientUI = MDApp.get_running_app()
        self.messages: dict[str, list[OneLineListItemAligned, ...]] = {
            self.app.user_id: [],
            self.other_user: [],
        }
        Window.bind(on_key_down=self._on_keyboard_down)
        self.times_validated = 0
        self.message_sent_spam = 0  # messages sent in spam_time
        self.allow_single_enter = True

    def _on_keyboard_down(self, instance, keyboard, keycode, text, modifiers):
        """Event press enter twice or use shift + enter to send message."""
        send_message = False
        chat_input: MDTextField
        chat_input = self.ids.chat_input
        if chat_input.focus:
            if keycode == 40 or keycode == 225:
                if self.allow_single_enter:
                    send_message = True
                else:
                    self.times_validated += 1

            data = {
                "type": "msg.typing.send",
                "room_id": self.name,
                "other_username": self.other_user,
                "other_id": self.app.get_other_user_id(self.name),
                "timestamp": str(datetime.now().timestamp()),
                "data": chat_input.text,
            }
            self.app.reset_theme()
            self.app.send_data(value=data)

        if not self.allow_single_enter and self.times_validated == 2:
            send_message = True
            self.times_validated = 0

        if send_message and chat_input.text:
            messages = self.messages[self.app.user_id]
            if len(messages) >= self.app.spam_count:
                secs = days_hours_minutes_seconds(
                    datetime.now()
                    - datetime.fromtimestamp(messages[-self.app.spam_count].timestamp)
                )[-1]
                if secs % 60 <= self.app.spam_time:
                    if self.message_sent_spam >= self.app.spam_count:
                        chat_input.readonly = True
                        chat_input.focus = False
                        chat_input.helper_text_color_normal = [1, 0, 0, 1]
                        chat_input.helper_text_color_focus = [1, 0, 0, 1]
                        chat_input.helper_text = (
                            r"Spamming detected... messaging disabled ¯ \ _ ( ツ ) _ / ¯"
                        )
                        Clock.schedule_once(self.enable_text_input, self.app.spam_time)
                    else:
                        self.message_sent_spam += 1

            self.send_message(self.ids.chat_input.text)

    def enable_text_input(self, dt):
        """Enables the chat input on a chat screen"""
        chat_input = self.ids.chat_input
        chat_input.readonly = False
        chat_input.helper_text = "Enter your message"
        chat_input.helper_text_color_normal = Colors.primary_bg
        chat_input.helper_text_color_focus = Colors.primary_bg
        chat_input.focus = True
        self.message_sent_spam = 0

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
            get_focus(self.ids.chat_input)
            self.app.send_data(value=msg_data)

    def add_message(
        self,
        message: str,
        user_id: str,
        text_color: list,
        halign: str = "left",
        clear_input: bool = False,
        message_id: str = "",
        timestamp: str = "",
    ) -> OneLineListItemAligned:
        """Adds a received message to the screen."""
        if clear_input:
            message = self.ids["chat_input"].text
            self.ids["chat_input"].text = ""

        chat_message = OneLineListItemAligned(
            halign,
            text=message,
            theme_text_color="Custom",
            text_color=text_color,
            message_id=message_id,
            timestamp=timestamp,
            user_id=user_id,
        )
        self.ids["chat_list"].add_widget(chat_message)

        if user_id == self.app.user_id:
            self.messages[self.app.user_id].append(chat_message)
        else:
            self.messages[self.other_user].append(chat_message)

        # increase message count in UI
        chat = ChatItem.Items.get(self.name)
        chat.msg_count = str(int(chat.msg_count) + 1)

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


class ProfileDialogContent(MDGridLayout):
    """Content for User Profile Dialog"""

    pass
