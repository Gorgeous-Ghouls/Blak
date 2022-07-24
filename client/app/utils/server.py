"""This is dummy server that is used when developing New API for client."""

import asyncio
import random

import websockets
from kivy import Logger


async def echo(websocket):
    """Send Random message back."""
    async for message in websocket:
        Logger.debug(f"DummyServer: Received {message}")
        await websocket.send(str(random.random()))


async def main():
    """Create and Host the server"""
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever


asyncio.run(main())
