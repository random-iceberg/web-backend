from unittest.mock import patch

from argon2.exceptions import VerifyMismatchError
from fastapi.testclient import TestClient
from pytest import fixture
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_service import create_user, mk_jwt_token

from .common import (
    ADMIN_CREDS,
    JWT_KEY,
    TEST_CREDS,
    UserData,
)


@fixture(autouse=True, scope="session")
def set_password_hasher():
    with patch("services.user_service.ph") as ph:

        def hash(x: str):
            return f"hashed-{x}"

        def verify(hashed_x: str, x: str):
            if hashed_x != f"hashed-{x}":
                raise VerifyMismatchError

        ph.hash.side_effect = hash
        ph.verify.side_effect = verify
        yield ph


@fixture()
async def admin_user(db_session: AsyncSession) -> UserData:
    creds = ADMIN_CREDS
    user = await create_user(db_session, creds.email, creds.password, role="admin")
    return UserData(creds=creds, role="admin", user=user)


@fixture()
async def user_user(db_session: AsyncSession) -> UserData:
    creds = TEST_CREDS
    user = await create_user(db_session, creds.email, creds.password, role="user")
    return UserData(creds=creds, role="user", user=user)


def mk_client(client: TestClient, user: UserData) -> TestClient:
    token = mk_jwt_token(user=user.user, jwt_key=JWT_KEY)
    client.cookies.set("access_token", token)
    return client


@fixture()
async def admin_client(client: TestClient, admin_user: UserData) -> TestClient:
    return mk_client(client, admin_user)


@fixture()
async def user_client(client: TestClient, user_user: UserData):
    return mk_client(client, user_user)


@fixture()
async def anon_client(client: TestClient):
    return client


@fixture()
async def mk_user(db_session: AsyncSession):
    async def f(index: int):
        mail = f"user{index}@example.com"
        password = "userpassword"
        user = await create_user(db_session, mail, password)
        token = mk_jwt_token(user=user, jwt_key=JWT_KEY)
        return token

    return f
