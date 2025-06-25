import os

from fastapi.testclient import TestClient
from pytest import fixture
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from db.helpers import init_db
from db.schemas import Base
from main import app

from .conf.auth import *  # noqa: F403
from .conf.common import JWT_KEY


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
    engine = create_async_engine(url)
    # Clean the database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    yield engine
    await engine.dispose()


@fixture()
async def async_session_test(async_engine_test):
    """Fixture for async database session for tests."""
    async_session_factory = await init_db(async_engine_test)

    async with async_session_factory() as session:
        yield session


@fixture()
async def db_session(async_session_test: AsyncSession):
    return async_session_test


@fixture()
async def client(postgres_container: PostgresContainer, async_engine_test):
    os.environ["JWT_SECRET_KEY"] = JWT_KEY

    with TestClient(app) as client:
        yield client
