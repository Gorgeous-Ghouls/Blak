import asyncio
from typing import Any

import websockets
from kivy import Logger
from kivy.app import App


class ClientUI(App):
    """Main Class to Build frontend on."""

    ws: websockets.WebSocketClientProtocol = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ws_handler_task = None

    def build(self):
        """Main function that is called when window for Kivy is being generated add/load kv files here"""
        pass

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
                except OSError:
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
