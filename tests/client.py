import os

from fastapi.testclient import TestClient
from pytest import fixture
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer

from db.schemas import Base
from main import app


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
async def client(postgres_container: PostgresContainer):
    os.environ["JWT_SECRET_KEY"] = "ultrasecuresecretkey"
    
    with TestClient(app) as client:
        yield client

    # Clean the database
    url = postgres_container.get_connection_url()
    engine = create_async_engine(url, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
