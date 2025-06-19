import logging
import time
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from os import environ
import uuid

from asyncpg.exceptions import InvalidPasswordError
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import create_async_engine

import db
from routers import auth, models, prediction
from services import user_service
from models.schemas import ErrorResponse

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

    # TODO: remove when the way to configure initial users is fininshed
    try:
        async with async_session() as session:
            _ = await user_service.create_user(
                session, "admin@test", "apass", role="admin"
            )
        async with async_session() as session:
            _ = await user_service.create_user(
                session, "user@test", "upass", role="user"
            )
    except Exception as e:
        logger.info(e)

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
        correlation_id = getattr(request.state, "correlation_id", None)
        start_time = time.time()
        client_ip = request.headers.get("x-forwarded-for") or (
            request.client.host if request.client else "unknown"
        )
        logger.info(
            f"Request: {request.method} {request.url.path} - Client: {client_ip} - Correlation ID: {correlation_id}"
        )

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - Process Time: {process_time:.4f}s - Correlation ID: {correlation_id}"
        )
        return response

    @app.middleware("http")
    async def add_correlation_id(request: Request, call_next):
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
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

    # Register exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        correlation_id = getattr(request.state, "correlation_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                code="HTTP_ERROR",
                timestamp=datetime.now(timezone.utc),
                correlation_id=correlation_id
            ).model_dump(mode='json'),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        correlation_id = getattr(request.state, "correlation_id", None)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail="An unexpected error occurred.",
                code="INTERNAL_SERVER_ERROR",
                timestamp=datetime.now(timezone.utc),
                correlation_id = correlation_id
            ).model_dump(mode='json'),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        correlation_id = getattr(request.state, "correlation_id", None)
        errors = exc.errors()
        field_errors = [
            f"{error['loc'][1]}: {error['msg']}" for error in errors
        ]
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                detail="Validation Error: " + ", ".join(field_errors),
                code="VALIDATION_ERROR",
                timestamp=datetime.now(timezone.utc),
                correlation_id=correlation_id
            ).model_dump(mode='json'),
        )
    return app


# Instantiate the application
app = create_app()
