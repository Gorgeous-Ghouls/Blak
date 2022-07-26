import asyncio
from typing import Any

import kivymd.uix.button
import websockets
from kivy import Logger
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.modules import inspector
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout

from ..utils import Colors, app_dir

Window.borderless = True
Window.custom_titlebar = True


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
            Builder.load_file(str(file))

        root = Builder.load_file(str(app_dir / "lib/kv_files/client_ui.kv"))
        root.md_bg_color = get_color_from_hex(Colors.primary_bg.value)
        if Window.set_custom_titlebar(root.ids["titlebar"]):
            Logger.info("Window: setting custom titlebar successful")
        else:
            Logger.info(
                "Window: setting custom titlebar " "Not allowed on this system "
            )
        inspector.create_inspector(Window, root)
        return root

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
                    await self.ws.recv()  # todo: write a wrapper to parse incoming data and update kivy accordingly
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
                    await asyncio.sleep(5)  # try after 5 secs
                    pass

            await asyncio.sleep(0)

    def send_data(self, instance: Any, value: str | int = None) -> None:
        """Wrapper around  WebSocketClientProtocol.send so that kivy event bindings work normally.

        :param instance Object that is sending the data
        :param value value that the object represents
        """
        if value is None:
            value = "test"

        async def send_data_wrapper(data):
            """Async function that actually sends data to the server"""
            if self.ws and self.ws.open:
                await self.ws.send(data)

        asyncio.create_task(send_data_wrapper(value))

    async def connection_lost(self):
        """Function called whenever connection with server is lost"""
        pass
        # todo enumerate things that are needed to be done when connection is lost

    @staticmethod
    async def connection_established():
        """Function called whenever connection with the server is established"""
        Logger.info("WS: Connected")
        # todo enumerate things that are needed to be done when connection is established

    async def add_chat(self):
        """Adds new user to Chat list container"""
        # todo complete addition of chats when a successful response or request to add a chat is received
        pass
