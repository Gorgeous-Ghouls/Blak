"""This is where the main backend app will go into"""

from fastapi import FastAPI, WebSocket
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .managers import ConnectionManager, DbManager

app = FastAPI()

db = DbManager("server/users.json", "server/rooms.json")
connections = ConnectionManager(db)


@app.route("/ws")
@app.route("/")
async def hello(*args):
    """Default http route"""
    return JSONResponse(content=jsonable_encoder({"data": "hello"}))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Websocket entrypoint"""
    await connections.create_session(websocket)


@app.on_event("shutdown")
async def close_db():
    """Saves the database"""
    db.save()
