import asyncio
import json
import uuid
from typing import Dict, List

from fastapi import WebSocket


class DbManager:
    """Manages the Database operations"""

    def __init__(self, user_db_file: str, rooms_db_file: str):
        self.user_db_file = user_db_file
        self.rooms_db_file = rooms_db_file
        self.users = {}
        self.rooms = {}
        try:
            with open(self.user_db_file) as u, open(self.rooms_db_file) as r:
                self.users = json.loads(u.read())
                self.rooms = json.loads(r.read())
        except (FileNotFoundError,json.JSONDecodeError) as e:
            print(e)

    def get_user(self, user_id: str = "") -> Dict:
        """Fetches the user data from Database"""
        if user_id:
            return self.users.get(user_id, None)
        else:
            return self.users

    def get_user_rooms(self, user_id: str) -> List:
        """Fetches the room data for a user from Database"""
        selected_rooms = []
        for i in self.rooms:
            if user_id in i:
                selected_rooms.append(self.rooms[i])
        return selected_rooms

    def create_room(self, sender_id: str, reciever_id: str) -> str:
        """Creates a new room(only if the persons don't already have one)"""
        room_id = sender_id + reciever_id
        if ((sender_id + reciever_id) in self.rooms) or (
            (reciever_id + sender_id) in self.rooms
        ):
            return None
        self.rooms[room_id] = {
            "room_id": room_id,
            "users": [sender_id, reciever_id],
            "messages": [],
        }
        return room_id

    def create_user(self, username: str, password: str) -> str:
        """Creates a new user"""
        user_id = str(uuid.uuid4())
        self.users[user_id] = {
            "user_id": user_id,
            "username": username,
            "password": password,
        }
        return user_id

    def get_latest_messages(self, room_id: str, n: int = 20) -> List:
        """Get latest "n" no of messages"""
        req_room = self.rooms[room_id]
        messages = req_room["messages"]
        return messages[-n:]

    def create_message(
        self, sender_id: str, message: str, timestamp: int, room_id: str
    ) -> str:
        """Adds a message created by the user to Database"""
        req_room = self.rooms[room_id]
        message_id = str(uuid.uuid4())
        req_room["messages"].append(
            {
                "message_id": message_id,
                "sender": sender_id,
                "message": message,
                "timestamp": timestamp,
            }
        )
        return message_id

    def save(self) -> None:
        """Saves the database"""
        with open(self.user_db_file, "w") as u, open(self.rooms_db_file, "w") as r:
            json.dump(self.users, u)
            json.dump(self.rooms, r)


class ConnectionManager:
    """Class which manages the users connections to the server"""

    def __init__(self, db: DbManager):
        self.db = db
        self.active_sessions = {}

    async def create_session(self, websocket: WebSocket) -> None:
        """Creates a client handler"""
        from .user import User

        session_id = str(uuid.uuid4())
        temp_gen = User.create(session_id, websocket, self.db, self)
        self.active_sessions[session_id] = await asyncio.create_task(anext(temp_gen))
        await asyncio.create_task(anext(temp_gen))

    def close_session(self, session_id: str) -> None:
        """Destroys the exisiting client handler"""
        self.active_sessions.pop(session_id, None)

    def is_user_online(self, user_id: str) -> WebSocket | None:
        """Checks for roomate is online"""
        for obj in self.active_sessions.values():
            if obj.logged_in:
                if user_id == obj.user_id:
                    return obj.websocket
        else:
            return None
