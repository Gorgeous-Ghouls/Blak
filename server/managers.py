import json
from typing import Dict, List

import aiofiles
from fastapi import WebSocket


class ConnectionManager:
    """Class which manages the users connections to the server"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, room_name: str) -> None:
        """Connects to the incoming client's connection request"""
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket, room_name: str) -> None:
        """Disconnects to the exisiting client's connection"""
        self.active_connections.remove(websocket)


class MessageManager:
    """Class which manages sending message to the correct user"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    async def send_message(self, message: str, other_user_id: str) -> None:
        """Sends messge to the requested user"""
        ...


class DbManager:
    """Manages the Database operations"""

    def __init__(self, user_db_file: str, messages_db_file: str):
        self.user_db_file = user_db_file
        self.rooms_db_file = messages_db_file

    async def get_user(self, user_id: str) -> Dict:
        """Fetches the user data from Database"""
        async with aiofiles.open(self.user_db_file, mode="r") as f:
            data = await f.read()
        users = json.loads(data)
        return users.get(user_id, {"error": "user not found"})

    async def get_room(self, room_id: str) -> Dict:
        """Fetches the room data from Database"""
        async with aiofiles.open(self.rooms_db_file, mode="r") as f:
            data = await f.read()
        rooms = json.loads(data)
        return rooms.get(room_id, {"error": "user not found"})

    async def create_room(self, sender_id: str, reciever_id: str) -> None:
        """Creates a new room(only if the persons don't already have one)"""
        async with aiofiles.open(self.rooms_db_file, mode="r") as f:
            data = await f.read()
        rooms = json.loads(data)
        room_id = sender_id + reciever_id
        if room_id in rooms:
            return {"error": "room already exists"}
        rooms[room_id] = {
            "room_id": room_id,
            "users": [sender_id, reciever_id],
            "messages": [],
        }
