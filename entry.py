from os import environ

import uvicorn

if __name__ == "__main__":
    if environ.get("ENVIRONMENT") == "production":
        uvicorn.run("main:app", host="0.0.0.0", port=8000)
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
