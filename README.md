## Install info
Both client and server, contain seperate pyproject.toml (must have poetry installed)
so just cd into dir and run

To run the install pacakges and run the client:
```
cd client
poetry install
poetry run blak
```
If you are hosting server on your own, change the contents of client/.env file to following:
```py
WEBSOCKET_HOST=<ip or url:port>

# the default is localhost:8000
```

and start the server by: (only needed if u want to run on localhost, as server is deployed)
```
cd server
poetry install
poetry run blak-server
```


# Gorgeous-Ghouls Project

### Team Members

- [p0lygun](https://github.com/p0lygun) (Gala on discord)
- [StoneSteel27](https://github.com/stonesteel27)
- [Alias](https://github.com/noahlias)
- [BlackPanther112358](https://github.com/BlackPanther112358)
