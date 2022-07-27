import pathlib

import uvicorn


def ensure_files():
    """Ensurers that runtime files exists."""
    app_dir = pathlib.Path(__file__).parent
    (app_dir / "users.json").touch(exist_ok=True)
    (app_dir / "rooms.json").touch(exist_ok=True)


def main():
    """Main run entrypoint for backend"""
    ensure_files()
    uvicorn.run("server.app:app", port=8000, log_level="info")


if __name__ == "__main__":
    main()
