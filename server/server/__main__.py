import os
import pathlib
import sys

import uvicorn
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


def ensure_files():
    """Ensurers that runtime files exists."""
    app_dir = pathlib.Path(__file__).parent
    (app_dir / "users.json").touch(exist_ok=True)
    (app_dir / "rooms.json").touch(exist_ok=True)


def main():
    """Main run entrypoint for backend"""
    logging_level = os.getenv("logging_level", "INFO")
    logger.remove()
    logger.add(sys.stderr, level=logging_level)

    ensure_files()
    uvicorn.run(
        "server.app:app", host="localhost", port=8000, log_level=logging_level.lower()
    )


if __name__ == "__main__":
    main()
