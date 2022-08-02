# Blak
## _The Remarkable Place to Prattle, Ever_

Blak is a cross-platform, FastAPI-powered, 
Websocket based Chat Application, made for **Python-Discord's Summer Code Jam 9**.


## Features

- Blak is for people who need to chat in private.
- Blak has no word wrap. So even if someone sends humongous text messages, It won't be visible. So, users can have a meaningful talk within a few messages.
- Users can see each others typing-in messages in real-time.

## Tech

Blak uses a number of open source projects to work properly:

- [Kivy] - Amazing open source UI framework written in Python
- [FastAPI] - Awesome web framework for buildingAPIs with Python
- [Websockets] - Library for building WebSocket servers and clients in Python.
- [Poetry] - Great pacakage manager for Python


And of course Blak itself is open source with a [public repository][Blak]
 on GitHub.

## Installation:

Blak requires [Python](https://python.org/) 3.10 to run.

Clone the repo, install the requirements using [Poetry] for the client and start the app
(server has been already implemented and running, so we can skip to the following part)
```sh
git clone https://github.com/Gorgeous-Ghouls/Blak.git
cd client
poetry install
poetry run blak
```
### Run with your own server:
Install requirements, and start the server
```sh
cd server
poetry install
poetry run blak-server
```
And in the `client/.env` file, change the replace `url:port` to server's running `url:port`
```sh
WEBSOCKET_HOST=<ip or url:port>
```

## Docker
TODO

## License

MIT


[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [Kivy]: <https://github.com/kivy/kivy>
   [FastAPI]: <https://github.com/tiangolo/fastapi>
   [Websockets]: <https://github.com/aaugustin/websockets>
   [Poetry]: <https://github.com/python-poetry/poetry>
   [Blak]: <https://github.com/Gorgeous-Ghouls/Blak>
