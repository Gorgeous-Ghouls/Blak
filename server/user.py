import json

from fastapi import WebSocket

from .managers import DbManager


class User(object):
    """Class which handles and setups the incoming client connection"""

    @classmethod
    async def create(cls, websocket: WebSocket, db: DbManager):
        """Asynchronous __init__ of User class"""
        self = User()
        self.websocket = websocket
        self.db = db

    async def wait_for_auth(self):
        """Authenticates(login or register) incoming connections from a user"""
        retry = True
        while retry:
            data = await self.websocket.receive_text()
            request = json.loads(data)
            user_data = {}
            if request["type"] == "user.login":
                users = self.db.get_user()
                for i in users:
                    if (
                        users[i]["username"] == request["username"]
                    ):  # there is a chance of matching two
                        if (
                            users[i]["password"] == request["password"]
                        ):  # diffrent accounts with same username and password
                            user_data["user_id"] = users[i]["user_id"]
                            user_data["username"] = users[i]["username"]
                            user_data["rooms"] = self.db.get_user_rooms(
                                user_data["user_id"]
                            )
                            await self.websocket.send_json(
                                {
                                    "type": "user.login.success",
                                    "data": user_data,
                                    "message": "Logged in succesfully",
                                }
                            )
                            retry = False
                            break
                else:
                    await self.websocket.send_json(
                        {
                            "type": "user.login.rejected",
                            "data": None,
                            "message": "Username or Password is wrong",
                        }
                    )
                    continue
            elif request["type"] == "user.register":
                user_id = self.db.create_user(request["username"], request["password"])
                user_data["user_id"] = user_id
                await self.websocket.send_json(
                    {
                        "type": "user.register.success",
                        "data": user_data,
                        "message": "registered succesfully",
                    }
                )
