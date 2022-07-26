import uvicorn


def main():
    """Main run entrypoint for backend"""
    uvicorn.run("server.app:app", port=8000, log_level="info")


if __name__ == "__main__":
    main()
