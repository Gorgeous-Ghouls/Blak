"""This is dummy server that is used when developing New API for client."""

import asyncio
import json
import uuid

import websockets


async def echo(websocket):
    """Send Random message back."""
    async for message in websocket:
        message = json.loads(message)
        reply = dict()
        match message["type"]:
            case "user.login":
                if message["username"] == "blak" and message["password"] == "blak":
                    reply.update(
                        {
                            "type": message["type"],
                            "username": message["username"],
                            "data": True,
                            "user-id": str(uuid.uuid4()),
                        }
                    )
                else:
                    reply.update(
                        {
                            "type": message["type"],
                            "data": False,
                            "user-id": None,
                        }
                    )

        await websocket.send(json.dumps(reply))


async def main():
    """Create and Host the server"""
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever


asyncio.run(main())
