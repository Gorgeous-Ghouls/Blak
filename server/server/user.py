import json
from functools import wraps

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from starlette.websockets import WebSocketState

from . import managers


def websocket_connection(method):
    """Wrapper for detecting and handling websocket closing"""

    @wraps(method)
    async def _impl(self, *method_args, **method_kwargs):
        try:
            method_output = await method(self, *method_args, **method_kwargs)
            return method_output
        except WebSocketDisconnect:
            try:
                logger.debug(f"Closing Connection {self.session_id}")
                self.close = True
                self.connections.close_session(self.session_id)
            except Exception as e:
                print(e)

    return _impl


class User(object):
    """Class which handles and setups the incoming client connection"""

    close: bool
    websocket: WebSocket
    db: managers.DbManager
    connections: managers.ConnectionManager
    logged_in: bool
    session_id: str
    username: str

    @classmethod
    async def create(
        cls,
        session_id: str,
        websocket: WebSocket,
        db: managers.DbManager,
        connections: managers.ConnectionManager,
    ):
        """Asynchronous __init__ of User class"""
        self = User()
        self.session_id = session_id
        self.connections = connections
        self.websocket = websocket
        await self.websocket.accept()
        self.logged_in = False
        self.db = db
        self.close = False
        yield self
        self.user_id = None
        self.user_id = await self.wait_for_auth()
        await self.handle_user(self.user_id)

    @websocket_connection
    async def wait_for_auth(self) -> str:
        """Authenticates(login or register) incoming connections from a user"""
        while not self.logged_in and not self.close:
            try:
                request = await self.websocket.receive_json()
                user_data = {}
                if request["type"] == "user.login":
                    users = self.db.get_user()
                    for i in users:
                        if users[i]["username"] == request["username"]:
                            if users[i]["password"] == request["password"]:
                                user_data["user_id"] = users[i]["user_id"]
                                user_data["username"] = users[i]["username"]
                                user_data["rooms"] = self.db.get_user_rooms(
                                    user_data["user_id"]
                                )
                                logger.info(f"{request['username']} logged in")
                                await self.websocket.send_json(
                                    {"type": "user.login.success", "data": user_data}
                                )
                                self.logged_in = True
                                return user_data["user_id"]
                    else:
                        await self.websocket.send_json(
                            {
                                "type": "user.login.rejected",
                                "data": None,
                                "message": "Username or Password is wrong",
                            }
                        )
                elif request["type"] == "user.register":
                    username_exists = self.db.does_username_exist(request["username"])
                    if not username_exists:
                        user_id = self.db.create_user(
                            request["username"], request["password"]
                        )
                        user_data["user_id"] = user_id
                        logger.info(f"account {request['username']} has been created")
                        self.username = request["username"]
                        await self.websocket.send_json(
                            {
                                "type": "user.register.success",
                                "data": user_data,
                                "message": "registered successfully",
                            }
                        )
                    else:
                        await self.websocket.send_json(
                            {
                                "type": "user.register.rejected",
                                "data": None,
                                "message": "username already exists",
                            }
                        )
            except json.JSONDecodeError:
                logger.debug("Wrong json data sent from client")

    @websocket_connection
    async def handle_user(self, user_id: str) -> None:
        """Handles requests from a logged-in user"""
        while not self.close:
            try:
                if self.websocket.client_state == WebSocketState.CONNECTED:
                    request = await self.websocket.receive_json()
                    if request["type"] == "msg.send":
                        roommate_websocket = self.connections.is_user_online(
                            request["other_id"]
                        )
                        message_id = self.db.create_message(
                            user_id,
                            request["data"],
                            request["timestamp"],
                            request["room_id"],
                        )
                        if roommate_websocket:
                            await roommate_websocket.send_json(
                                {
                                    "type": "msg.recv",
                                    "message_id": message_id,
                                    "user_id": user_id,
                                    "data": request["data"],
                                    "room_id": request["room_id"],
                                    "timestamp": request["timestamp"],
                                }
                            )
                        await self.websocket.send_json(
                            {"type": "msg.sent", "message_id": message_id}
                        )
                    elif request["type"] == "room.create":
                        room_id = self.db.create_room(
                            request["user_id"], request["data"]
                        )
                        await self.websocket.send_json(
                            {"type": "room.create.success", "room_id": room_id}
                        )
                        self.db.save()
            except json.JSONDecodeError:
                logger.debug(f"Wrong json data sent by {self.username}")
