import asyncio
import json
from typing import Any, TypedDict
from uuid import UUID

import kivymd.uix.button
import websockets
from kivy import Logger
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.modules import inspector
from kivy.properties import BooleanProperty, StringProperty
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout

from ..utils import Colors, app_dir

Window.borderless = True
Window.custom_titlebar = True


class KivyIds(TypedDict):
    """Class to track ids defined in kv files"""

    # todo ask can how can this be used to auto-complete dict keys
    titlebar: str
    chat_list_container: str
    main_box: str
    app_screen_manager: str
    chats_screen_manager: str
    username: str
    password: str


class TitleBar(MDFloatLayout):
    """Custom TitleBar for the app"""

    md_bg_color = get_color_from_hex(Colors.accent_bg.value)
    button_bg = get_color_from_hex(Colors.primary_bg.value)
    button_size = "15sp"

    def __init__(self, **kwargs):
        super(TitleBar, self).__init__(**kwargs)
        self.app: MDApp = MDApp.get_running_app()

    def handle_buttons(self, instance: kivymd.uix.button.BaseButton):
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


class ClientUI(MDApp):
    """Main Class to Build frontend on."""

    ws: websockets.WebSocketClientProtocol = None
    login: bool = BooleanProperty(False)
    user_name: str = StringProperty()
    user_id: UUID = None
    login_helper_text: str = StringProperty()
    login_data_sent: bool = BooleanProperty(
        False
    )  # very inefficient way to stop spamming

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
        root.md_bg_color = get_color_from_hex(Colors.primary_bg.value)
        if Window.set_custom_titlebar(root.ids["titlebar"]):
            Logger.info("Window: setting custom titlebar successful")
        else:
            Logger.info(
                "Window: setting custom titlebar " "Not allowed on this system "
            )
        inspector.create_inspector(Window, root)
        return root

    def on_start(self):
        """Called just before the app window is shown"""
        self.root.ids["app_screen_manager"].current = "login"

    async def app_func(self) -> tuple[BaseException | Any, BaseException | Any]:
        """A wrapper function to start websocket client and kivy simultaneously

        run_wrapper starts kivy app and waits for it to finish
        ws_handler_task handles receiving of data from server
        """
        self.ws_handler_task = asyncio.ensure_future(self.ws_handler())

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

                except Exception as e:
                    Logger.warn(f"ws_handler: Something happened {e}")
            if connection_closed:
                try:
                    self.ws = await websockets.connect("ws://localhost:8765")
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
            Logger.info(f"hrd: {reply}")
            match reply["type"]:
                case "user.login":
                    if reply["data"]:  # login Successful
                        self.user_id = UUID(reply["user-id"])
                        self.user_name = reply["username"]
                        self.login = True
                    else:
                        self.login_helper_text = "Invalid Username or Password"
                        # todo clear username and password fields
                        self.login_data_sent = False

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
                Logger.info(f"sdw: {data}")
            except json.JSONDecodeError:
                Logger.warn(f"Wrong Data send {type(data)}")

            await self.ws.send(data)

    async def connection_lost(self):
        """Function called whenever connection with server is lost"""
        self.login_data_sent = True
        # todo enumerate things that are needed to be done when connection is lost

    async def connection_established(self):
        """Function called whenever connection with the server is established"""
        Logger.info("WS: Connected")
        self.login_data_sent = False
        # todo enumerate things that are needed to be done when connection is established

    async def add_chat(self):
        """Adds new user to Chat list container"""
        # todo complete addition of chats when a successful response or request to add a chat is received
        pass

    def on_login(self, instance, value):
        """Sets correct login screen whenever app.login changes"""
        if value:
            self.root.ids["app_screen_manager"].current = "app"
        else:
            self.root.ids["app_screen_manager"].current = "login"

    def do_login(self, username: str, password: str):
        """Login the user and set app.login accordingly"""
        if not self.login_data_sent and (len(username) and len(password)):
            data = {
                "type": "user.login",
                "username": username,
                "password": password,
            }
            if self.ws and self.ws.open:
                self.login_data_sent = True
            self.send_data(value=data)
