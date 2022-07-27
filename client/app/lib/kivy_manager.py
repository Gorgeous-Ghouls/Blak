import asyncio
import json
from typing import Any, TypedDict
from uuid import UUID

import websockets
from app import ui
from kivy import Logger
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.modules import inspector
from kivy.properties import BooleanProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout

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


class ClientUI(MDApp):
    """Main Class to Build frontend on."""

    root: MDBoxLayout
    ws: websockets.WebSocketClientProtocol = None
    login: bool = BooleanProperty(False)
    user_name: str = StringProperty()
    user_id: UUID = None
    login_helper_text: str = StringProperty()
    login_data_sent: bool = BooleanProperty(
        False
    )  # very inefficient way to stop spamming

    connection_status: str = StringProperty("Disconnected")

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
        Clock.schedule_once(
            lambda dt: self.root._trigger_layout()
        )  # needed to make sure custom titlebar renders properly on windows and mac
        self.root.ids["app_screen_manager"].current = "app"

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
        self.connection_status = "Disconnected"
        self.root.ids["titlebar"].ids["connection_status_label"].color = [
            1,
            0,
            0,
            1,
        ]  # red
        # todo enumerate things that are needed to be done when connection is lost

    async def connection_established(self):
        """Function called whenever connection with the server is established"""
        Logger.info("WS: Connected")
        self.connection_status = "Connected"
        self.root.ids["titlebar"].ids[
            "connection_status_label"
        ].color = Colors.get_kivy_color("accent_bg_text")
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

    def do_logout(self):
        """Reset User info and go back to log in screen"""
        self.user_name = ""
        self.user_id = UUID(int=0)
        self.login = False

        # remove all chats and chat messages
        self.root.ids["chat_list_container"].clear_widgets()
        self.root.ids["chats_screen_manager"].clear_widgets()
