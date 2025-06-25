import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient
from pytest import fixture
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from db.helpers import init_db
from db.schemas import Base
from main import app
from services.user_service import create_user


@fixture(scope="session")
def postgres_container():
    postgres = PostgresContainer("postgres:17-alpine", driver="asyncpg")
    _ = postgres.start()

    os.environ["DB_ADDRESS"] = postgres.get_container_host_ip()
    os.environ["DB_PORT"] = str(postgres.get_exposed_port(5432))
    os.environ["DB_DATABASE"] = postgres.dbname
    os.environ["DB_USER"] = postgres.username
    os.environ["DB_PASSWORD"] = postgres.password

    yield postgres

    postgres.stop()


@fixture()
async def async_engine_test(postgres_container: PostgresContainer):
    """Fixture for async database engine for tests."""
    url = postgres_container.get_connection_url()
    engine = create_async_engine(url, echo=False)
    yield engine
    await engine.dispose()


@fixture()
async def async_session_test(async_engine_test):
    """Fixture for async database session for tests."""
    async_session_factory = await init_db(async_engine_test)

    async with async_session_factory() as session:
        yield session


@fixture()
async def admin_user_token(async_session_test: AsyncSession):
    """Fixture to create an admin user and return their JWT token."""
    admin_email = "admin@example.com"
    admin_password = "adminpassword"
    jwt_secret_key = os.environ["JWT_SECRET_KEY"]

    admin_user = await create_user(
        async_session_test, admin_email, admin_password, role="admin"
    )

    payload = {
        "sub": str(admin_user.id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "role": admin_user.role,
    }
    token = jwt.encode(payload, jwt_secret_key, algorithm="HS256")
    return token

@fixture()
async def mk_user(async_session_test: AsyncSession):
    async def f(index):
        mail = f"user{index}@example.com"
        password = "userpassword"
        jwt_secret_key = os.environ["JWT_SECRET_KEY"]

        user = await create_user(
            async_session_test, mail, password
        )

        payload = {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "role": user.role,
        }
        token = jwt.encode(payload, jwt_secret_key, algorithm="HS256")
        return token
    return f

@fixture()
async def client(postgres_container: PostgresContainer, async_engine_test):
    os.environ["JWT_SECRET_KEY"] = "ultrasecuresecretkey"

    with TestClient(app) as client:
        yield client

    # Clean the database
    async with async_engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
