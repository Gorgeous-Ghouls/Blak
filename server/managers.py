import json
import uuid
from typing import Dict, List

from fastapi import WebSocket


class ConnectionManager:
    """Class which manages the users connections to the server"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Connects to the incoming client's connection request"""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, websocket: WebSocket) -> None:
        """Disconnects to the exisiting client's connection"""
        for user_id in self.active_connections:
            if self.active_connections[user_id] == websocket:
                del self.active_connections[user_id]


class MessageManager:
    """Class which manages sending message to the correct user"""

    def __init__(self):
        self.message: Dict

    async def recieve_message(self, msg: json) -> None:
        """Processes the recieved message, sends to user if online, else stores in the db"""
        self.message = json.load(msg)

    async def send_message(self, websocket: WebSocket) -> None:
        """Sends messge to the requested user"""
        await websocket.send_json(json.dumps(self.message))


class DbManager:
    """Manages the Database operations"""

    def __init__(self, user_db_file: str, rooms_db_file: str):
        self.user_db_file = user_db_file
        self.rooms_db_file = rooms_db_file
        u = open(user_db_file)
        r = open(rooms_db_file)
        self.users = json.loads(u.read())
        self.rooms = json.loads(r.read())
        u.close()
        r.close()
        print("entering")

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

    def create_room(self, sender_id: str, reciever_id: str) -> None:
        """Creates a new room(only if the persons don't already have one)"""
        room_id = sender_id + reciever_id
        if ((sender_id + reciever_id) in self.rooms) or (
            (reciever_id + sender_id) in self.rooms
        ):
            return {"error": "room already exists"}
        self.rooms[room_id] = {
            "room_id": room_id,
            "users": [sender_id, reciever_id],
            "messages": [],
        }
        return room_id

    def create_user(self, username: str, password: str) -> Dict:
        """Creates a new user"""
        for i in self.users:
            if username in self.users[i]["username"]:
                return {"error": "This username already exists"}
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
    ) -> Dict:
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

    def close(self) -> None:
        """Closes and saves the database"""
        u = open(self.user_db_file, "w")
        json.dump(self.users, u)
        r = open(self.rooms_db_file, "w")
        json.dump(self.rooms)
        u.close()
        r.close()
