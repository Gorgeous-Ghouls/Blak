import asyncio
import json
import os
import sys
import traceback
from typing import Any, TypedDict
from uuid import UUID

import websockets
from app import ui
from dotenv import load_dotenv
from kivy import Logger
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.modules import inspector
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import get_random_color, platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.textfield import MDTextField

from ..utils import Colors, app_dir

load_dotenv()
Window.borderless = True
Window.custom_titlebar = True


class KivyIds(TypedDict):
    """Class to track ids defined in kv files"""

    # todo ask can how can this be used to auto-complete dict keys
    titlebar: ui.TitleBar
    chat_list_container: MDGridLayout
    main_box: MDBoxLayout
    app_screen_manager: ScreenManager
    chats_screen_manager: ScreenManager
    username: MDTextField
    password: MDTextField


class ClientUI(MDApp):
    """Main Class to Build frontend on."""

    root: MDBoxLayout
    ws: websockets.WebSocketClientProtocol = None
    login: bool = BooleanProperty(False)
    username: str = StringProperty()
    user_id: str = StringProperty()
    login_helper_text: str = StringProperty()
    login_data_sent: bool = BooleanProperty(
        False
    )  # very inefficient way to stop spamming

    rooms: list
    connection_status: str = StringProperty("Disconnected")
    idle_timeout: int = NumericProperty(5)
    idle_time: int = NumericProperty()
    theme_changed: bool = BooleanProperty(False)
    spam_time: int = NumericProperty(5)  # check for messages in the time frame (secs)
    spam_count: int = NumericProperty(
        5
    )  # max number of message that one can send in spam_time

    def __init__(self, **kwargs):
        super().__init__(title="Blak", **kwargs)
        self.ws_handler_task = None
        self.root: MDBoxLayout

    def build(self):
        """Main function that is called when window for Kivy is being generated add/load kv files here"""
        root: MDBoxLayout

        for file in (app_dir / "ui/kv_files").glob(
            "*.kv"
        ):  # Load all UI files before Loading root
            if file.stem == "client_ui":
                continue
            Builder.load_file(str(file))
        # load root explicitly
        root = Builder.load_file(str(app_dir / "ui/kv_files/client_ui.kv"))
        root.ids["titlebar"]: ui.TitleBar
        if platform in ["win", "linux"]:  # only set title bar on Windows and linux
            if Window.set_custom_titlebar(root.ids["titlebar"]):
                Logger.info("Window: setting custom titlebar successful")
            else:
                Logger.info(
                    "Window: setting custom titlebar " "Not allowed on this system "
                )
        else:
            root.remove_widget(root.ids["titlebar"])
            Window.borderless = False
            Window.custom_titlebar = False
        inspector.create_inspector(Window, root)
        return root

    def on_start(self):
        """Called just before the app window is shown"""
        Logger.info(f"ws host: {os.getenv('WEBSOCKET_HOST', 'localhost')}")
        Window.bind(on_motion=self.on_motion)
        Clock.schedule_interval(
            lambda dt: self.invert_theme(), 1
        )  # try to invert theme every second
        if Window.custom_titlebar:
            self.root.ids["titlebar"]: ui.TitleBar
            Clock.schedule_once(
                lambda dt: self.root.ids["titlebar"].fix_layout()
            )  # needed to make sure custom titlebar renders properly on Windows
        self.root.ids["app_screen_manager"].current = "login"

    def on_motion(self, *args):
        """Triggered every time there is any kind of motion on the window"""
        self.reset_theme()

    async def app_func(self) -> tuple[BaseException | Any, BaseException | Any]:
        """A wrapper function to start websocket client and kivy simultaneously

        run_wrapper starts kivy app and waits for it to finish
        ws_handler_task handles receiving of data from server
        """
        self.ws_handler_task = asyncio.create_task(self.ws_handler())

        async def run_wrapper():
            """Function to start kivy"""
            await self.async_run()
            self.ws_handler_task.cancel()

        return await asyncio.gather(run_wrapper(), self.ws_handler_task)

    async def ws_handler(self):
        """Function to handle incoming data from server.

        this function will try to reconnect with the server if connection is lost
        """
        connection_closed = True
        while True:
            if self.ws:
                try:
                    await self.handle_recv_data(
                        await self.ws.recv()
                    )  # todo: write a wrapper to parse incoming data and update kivy accordingly
                except websockets.ConnectionClosed:
                    await self.connection_lost()
                    connection_closed = True
                except asyncio.exceptions.CancelledError:
                    await self.ws.close()
                    break

                except Exception:
                    Logger.warn(
                        f"ws_handler: Something happened \n{traceback.format_exc()}"
                    )
            if connection_closed:
                try:
                    self.ws = await websockets.connect(
                        f"ws://{os.getenv('WEBSOCKET_HOST', 'localhost:8000')}/ws"
                    )
                    await self.connection_established()
                    connection_closed = False
                except (OSError, asyncio.exceptions.CancelledError):
                    await self.connection_lost()
                    await asyncio.sleep(
                        5
                    )  # try after 5 secs todo implement a timeout algo
                    pass

            await asyncio.sleep(0)

    async def handle_recv_data(self, reply: str):
        """Handles data sent by server"""
        # todo complete data handling
        try:
            reply = json.loads(reply)
            Logger.debug(f"hrd: {reply}")
            chats_screen_manager: ScreenManager
            chats_screen_manager = self.root.ids["chats_screen_manager"]
            match reply["type"]:
                case "msg.typing.recv":
                    if (
                        chats_screen_manager.current == reply["room_id"]
                    ):  # only show typing on the active chat
                        screen: ui.ChatMessagesScreen
                        screen = chats_screen_manager.get_screen(reply["room_id"])
                        screen.ids["typing"].text = reply["data"]

                case "msg.recv":
                    if not chats_screen_manager.has_screen(reply["room_id"]):
                        self.add_chat_screen(
                            reply["room_id"],
                            self.get_other_user_id(reply["room_id"]),
                            reply["sender_username"],
                        )

                    screen = chats_screen_manager.get_screen(reply["room_id"])
                    screen.add_message(reply["data"], Colors.text_dark)
                    screen.ids["typing"].text = ""
                case "msg.sent":
                    # add message to self screen only when we get confirmation from server
                    screen = chats_screen_manager.get_screen(reply["room_id"])
                    screen.add_message(
                        "",
                        Colors.text_medium,
                        clear_input=True,
                        halign="right",
                    )
                    screen.disable_chat_input = False

                case "user.login.success":
                    if data := reply["data"]:  # login Successful
                        self.title += f" {data['user_id']}"
                        self.user_id = data["user_id"]

                        self.username = data["username"]
                        self.rooms = data["rooms"]

                        # add user profile button
                        if Window.custom_titlebar:
                            self.root.ids["titlebar"].ids["profile_button"].bind(
                                on_release=ui.Dialog(
                                    title="Profile",
                                    type="custom",
                                    content_cls=ui.ProfileDialogContent(),
                                ).open
                            )
                        for room in self.rooms:
                            room_id = room["room_id"]
                            other_username = next(
                                username
                                for username in room["usernames"]
                                if username != self.username
                            )
                            other_id = self.get_other_user_id(room_id)
                            self.add_chat_screen(room_id, str(other_id), other_username)
                            msg = None
                            screen: ui.ChatMessagesScreen
                            screen = chats_screen_manager.get_screen(room_id)
                            for message in room["messages"]:
                                if message["sender"] == str(self.user_id):
                                    msg = screen.add_message(
                                        message["message"],
                                        Colors.text_medium,
                                        halign="right",
                                    )
                                else:
                                    msg = screen.add_message(
                                        message["message"],
                                        Colors.text_dark,
                                    )
                            if msg:
                                screen.scroll_to_message(msg)

                        self.login = True
                case "user.login.rejected":
                    self.login_helper_text = "Invalid Username or Password"
                    login_screen: ui.LoginScreen
                    login_screen = (
                        self.root.ids["app_screen_manager"]
                        .get_screen("login")
                        .children[0]
                    )
                    login_screen.reset_fields()
                    self.do_logout(close_connection=False)
                    self.login_data_sent = False
                case "user.register.success":
                    self.login_helper_text = "Registration Successful"

                    login_screen: ui.LoginScreen
                    login_screen = (
                        self.root.ids["app_screen_manager"]
                        .get_screen("login")
                        .children[0]
                    )
                    login_screen.reset_fields()
                    login_screen.ids["button_container"].remove_widget(
                        login_screen.ids["register_button"]
                    )
                    self.login_data_sent = False

                case "room.create.success":
                    room_id: str
                    if room_id := reply["room_id"]:
                        self.add_chat_screen(
                            room_id,
                            self.get_other_user_id(room_id),
                            reply["other_username"],
                        ).current = room_id
                        self.dismiss_top_popup()

        except json.JSONDecodeError:
            Logger.warn(f"Wrong Json data {reply}")

    def send_data(self, instance: Any = None, value: str | int | dict = None) -> None:
        """Wrapper around  WebSocketClientProtocol.send so that kivy event bindings work normally.

        :param instance Object that is sending the data
        :param value value that the object represents
        """
        if value is None:
            value = "test"

        asyncio.create_task(self.send_data_wrapper(value))

    async def send_data_wrapper(self, data):
        """Async function that actually sends data to the server"""
        if self.ws and self.ws.open:
            try:

                data = json.dumps(data)
                Logger.debug(f"sdw: {data}")
            except json.JSONDecodeError:
                Logger.warn(f"Wrong Data send {type(data)}")

            await self.ws.send(data)

    async def connection_lost(self):
        """Function called whenever connection with server is lost"""
        try:
            self.login_data_sent = True
            self.connection_status = "Disconnected"
            if Window.custom_titlebar:
                self.root.ids["titlebar"].ids["connection_status_label"].color = [
                    1,
                    0,
                    0,
                    1,
                ]  # red
            else:
                self.set_window_title()
            # todo enumerate things that are needed to be done when connection is lost
        except AttributeError:  # when ws_handler_task exits after run_wrapper is finished
            sys.exit(0)

    async def connection_established(self):
        """Function called whenever connection with the server is established"""
        Logger.info("WS: Connected")
        self.connection_status = "Connected"
        if Window.custom_titlebar:
            self.root.ids["titlebar"].ids[
                "connection_status_label"
            ].color = Colors.accent_bg_text
        else:
            self.set_window_title()
        self.login_data_sent = False
        # todo enumerate things that are needed to be done when connection is established

    def add_chat(self, user_id: str):
        """Adds new user to Chat list container"""
        # todo complete addition of chats when a successful response or request to add a chat is received
        pass

    async def add_chat_wrapper(self, user_id: str):
        """Adds new user to Chat list container"""
        # todo complete addition of chats when a successful response or request to add a chat is received
        pass

    async def check_user_id(self, user_id: str, dialog: ui.Dialog):
        """Sends request to the server to check if user with user_id exists"""
        try:
            UUID(user_id)
        except ValueError:
            Logger.warn(f"Wrong User id {user_id}")
            dialog.content_cls.ids["user_id_input"].helper_text = "Wrong User id"
            dialog.content_cls.ids["user_id_input"].helper_text_color_normal = [
                1,
                0,
                0,
                1,
            ]
            return
        request_data = {
            "type": "room.create",
            "user_id": str(self.user_id),
            "other_id": str(user_id),
        }

        await self.send_data_wrapper(request_data)

    def on_login(self, instance, value):
        """Sets correct login screen whenever app.login changes"""
        if value:
            self.root.ids["app_screen_manager"].current = "app"
        else:
            self.root.ids["app_screen_manager"].current = "login"

    def do_login(self, username: str, password: str, register: bool = False):
        """Login the user and set app.login accordingly"""
        if not self.login_data_sent and (len(username) and len(password)):
            data = {
                "type": "user.register" if register else "user.login",
                "username": username,
                "password": password,
            }
            if self.ws and self.ws.open:
                self.login_data_sent = True
            self.send_data(value=data)

    def do_logout(self, close_connection: bool = True):
        """Reset User info and go back to log in screen"""
        self.username = ""
        self.user_id = ""
        self.login = False
        if close_connection:
            asyncio.create_task(self.ws.close())

        # remove all chats and chat messages
        self.root.ids["chat_list_container"].clear_widgets()
        self.root.ids["chats_screen_manager"].clear_widgets()

    def set_window_title(self):
        """Sets window title when custom_titlebar is not used"""
        if not Window.custom_titlebar:
            self.title += f" - {self.connection_status}"

    # callbacks
    def show_add_chat_dialog(self):
        """Shows a dialog to add a new chat"""
        dialog = ui.Dialog(
            title="Add new Chat",
            type="custom",
            content_cls=ui.NewChatInputFields(),
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=Colors.text_medium,
                ),
                MDFlatButton(
                    text="Add",
                    theme_text_color="Custom",
                    text_color=Colors.text_medium,
                ),
            ],
        )
        btn: MDFlatButton
        for btn in dialog.buttons:
            match btn.text:
                case "CANCEL":
                    btn.bind(on_release=lambda i: dialog.dismiss())
                case "Add":
                    btn.bind(
                        on_release=lambda i: asyncio.create_task(
                            self.check_user_id(
                                dialog.content_cls.ids["user_id_input"].text, dialog
                            )
                        )
                    )
        dialog.open()

    def dismiss_top_popup(self):
        """Dismiss top-most active popup"""
        if isinstance(self.root_window.children[0], ui.Dialog):
            self.root_window.children[0].dismiss()

    def add_chat_screen(
        self, room_id: str, other_user: str, other_username: str
    ) -> ScreenManager:
        """Adds chat and its screen to the app"""
        chats_screen: ScreenManager
        chats_screen = self.root.ids["chats_screen_manager"]
        if not chats_screen.has_screen(room_id):
            self.root.ids["chat_list_container"].add_widget(
                ui.ChatItem(username=other_username, custom_id=room_id)
            )
            chats_screen.add_widget(
                ui.ChatMessagesScreen(other_user=other_user, name=room_id)
            )
        return chats_screen

    def get_other_user_id(self, room_id: str) -> str:
        """Returns user id of other user in a chat

        :param room_id id of the room to get the other user from
        """
        return room_id.replace(str(self.user_id), "")

    # it's not a bug it's a feature 😎
    def invert_theme(self):
        """Changes the client theme when left client is idle"""
        if not self.theme_changed:
            if self.idle_time > self.idle_timeout:
                anim = Animation(
                    primary_bg=get_random_color(1),
                    accent_bg=get_random_color(1),
                    duration=0.5,
                )
                anim.start(Colors)
                self.theme_changed = True
            else:
                self.idle_time += 1

    def reset_theme(self):
        """Resets the theme back to defaults"""
        self.idle_time = 0
        if self.theme_changed:
            Colors.reset()
            self.theme_changed = False
