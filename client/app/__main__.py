import asyncio
import os

if __name__ == "__main__":
    os.environ["SDL_VIDEO_X11_WMCLASS"] = "Blak"
    from .lib.kivy_manager import ClientUI

    client = ClientUI()
    try:
        asyncio.run(client.app_func())
    except asyncio.exceptions.CancelledError:
        pass
