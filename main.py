from contextlib import asynccontextmanager
import logging
import time
from os import environ

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import create_async_engine

import db
from routers import prediction, models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init
    user = environ["DB_USER"]
    database = environ["DB_DATABASE"]
    address = environ["DB_ADDRESS"]
    password_file = environ["DB_PASSWORD_FILE"]
    with open(password_file) as f:
        password = f.read(1024)

    engine = create_async_engine(
        f"postgresql+asyncpg://{user}:{password}@{address}/{database}",
        echo=True,
    )
    async_session = await db.helpers.init_db(engine)

    await db.helpers.populate_features(async_session)

    # Available in Request.state
    yield {"async_session": async_session}

    # Clean
    await engine.dispose()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.

    TODO:
      - Initialize middleware (e.g. CORS, logging, error handling).
      - Configure any global settings (database connections, security, etc.).
    """
    app = FastAPI(
        title="Titanic Survivor Prediction Backend",
        description="Production-ready backend API for Titanic survival prediction.",
        version="1.0.0",
        lifespan=lifespan,
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

    include_routers(app)

    @app.get("/", include_in_schema=False)  # Exclude from OpenAPI schema, Because.
    async def root_redirect():
        return RedirectResponse(url="/docs")

    return app


def include_routers(app: FastAPI) -> None:
    """
    Include API routers.

    TODO:
      - Include additional routers for authentication, administration, health checks, etc.
    """
    app.include_router(prediction.router, prefix="/predict", tags=["Prediction"])
    app.include_router(models.router, prefix="/models", tags=["Model Management"])


# Instantiate the application
app = create_app()
