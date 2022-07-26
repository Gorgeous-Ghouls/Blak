"""This is where the main backend app will go into"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from .managers import ConnectionManager, DbManager

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" cols="40" rows="5" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""
db = DbManager("server/users.json", "server/rooms.json")
connections = ConnectionManager(db)


@app.get("/")
async def get():
    """Normal /get"""
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Websocket entrypoint"""
    await connections.create_session(websocket)


@app.on_event("shutdown")
async def close_db():
    """Closes the database"""
    db.close()
