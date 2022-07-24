import asyncio
import os


def main():
    """A runner function that serves as an entry point for command scripts"""
    os.environ[
        "SDL_VIDEO_X11_WMCLASS"
    ] = "Blak"  # required when using a tiling manager or WM
    from .lib.kivy_manager import ClientUI

    client = ClientUI()
    try:
        asyncio.run(client.app_func())
    except asyncio.exceptions.CancelledError:
        pass


if __name__ == "__main__":
    main()
