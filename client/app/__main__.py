import asyncio

from .lib.kivy_manager import ClientUI

if __name__ == "__main__":
    client = ClientUI()
    try:
        asyncio.run(client.app_func())
    except asyncio.exceptions.CancelledError:
        pass
