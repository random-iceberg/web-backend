from os import environ

import uvicorn

if __name__ == "__main__":
    root_path = environ.get("BACKEND_WEB_ROOT", "")

    if environ.get("ENVIRONMENT") == "production":
        uvicorn.run("main:app", host="0.0.0.0", port=8000, root_path=root_path)
    else:
        uvicorn.run(
            "main:app", host="0.0.0.0", port=8000, reload=True, root_path=root_path
        )
