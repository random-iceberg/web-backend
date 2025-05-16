import os
from typing import Any

from fastapi.testclient import TestClient
from pytest import FixtureRequest, fixture
from testcontainers.postgres import PostgresContainer

from main import app


@fixture()
def postgres_container(request: FixtureRequest):
    """To test"""

    postgres = PostgresContainer("postgres:16-alpine")
    _ = postgres.start()

    def remove_container():
        postgres.stop()

    request.addfinalizer(remove_container)
    os.environ["DB_ADDRESS"] = postgres.get_container_host_ip()
    os.environ["DB_PORT"] = str(postgres.get_exposed_port(5432))
    os.environ["DB_DATABASE"] = postgres.dbname
    os.environ["DB_USER"] = postgres.username
    os.environ["DB_PASSWORD"] = postgres.password


@fixture()
def client(postgres_container: Any):
    _ = postgres_container

    with TestClient(app) as client:
        yield client
