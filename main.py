import logging
import time
from contextlib import asynccontextmanager
from os import environ

from asyncpg.exceptions import InvalidPasswordError
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import create_async_engine

import db
from routers import auth, models, prediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    user = environ.get("DB_USER")
    database = environ.get("DB_DATABASE")
    address = environ.get("DB_ADDRESS")
    password = environ.get("DB_PASSWORD")
    port = environ.get("DB_PORT")
    jwt_key = environ.get("JWT_SECRET_KEY")

    if not user or not database or not address:
        msg = (
            f"Missing database configuration: "
            f"DB_USER={user!r}, DB_DATABASE={database!r}, DB_ADDRESS={address!r}"
        )
        logger.error(msg)
        raise RuntimeError(msg)

    if not password:
        msg = f"No DB_PASSWORD provided for user '{user}'"
        logger.error(msg)
        raise RuntimeError(msg)
    
    if not jwt_key:
        msg = "No JWT_SECRET_KEY provided in environment variables."
        logger.error(msg)
        raise RuntimeError(msg)
    
    if port:
        address = f"{address}:{port}"

    url = f"postgresql+asyncpg://{user}:{password}@{address}/{database}"
    try:
        engine = create_async_engine(url, echo=True)
        async_session = await db.helpers.init_db(engine)
    except InvalidPasswordError:
        # The password was provided but authentication failed
        msg = f"Invalid password provided for DB user '{user}': {password!r}"
        logger.error(msg)
        raise RuntimeError(msg)
    except Exception as exc:
        # Bubble up other connection errors
        msg = f"Failed to connect to the database: {exc}"
        logger.error(msg)
        raise RuntimeError(msg)

    # Make session available on request.state
    yield {"async_session": async_session, "jwt_key": jwt_key}

    # Clean up
    await engine.dispose()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    """
    app = FastAPI(
        title="Titanic Survivor Prediction Backend",
        description="Production-ready backend API for Titanic survival prediction.",
        docs_url="/docs",
        redoc_url=None,
        swagger_ui_parameters={
            "syntaxHighlight": True,
            "docExpansion": "none",
        },
        version="1.0.0",
        lifespan=lifespan,
    )

    origins = environ.get("ALLOWED_ORIGINS", "*").split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # logging middleware shifted here from models.py, Recommended by Lev
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        client_ip = request.headers.get("x-forwarded-for") or (
            request.client.host if request.client else "unknown"
        )
        logger.info(
            f"Request: {request.method} {request.url.path} - Client: {client_ip}"
        )

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - Process Time: {process_time:.4f}s"
        )
        return response

    # include routers (prediction & models)
    app.include_router(prediction.router, prefix="/predict", tags=["Prediction"])
    app.include_router(models.router, prefix="/models", tags=["Model Management"])
    app.include_router(auth.router, prefix="/auth", tags=["User Authentication"])

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Simple health check endpoint to verify the service is running.
        """
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return RedirectResponse(url="/docs")

    return app


# Instantiate the application
app = create_app()