from collections.abc import Callable
from unittest.mock import patch

import pytest
from argon2 import PasswordHasher
from argon2.profiles import CHEAPEST
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from pytest import fixture

from models.schemas import UserCredentials

from .conf.common import TEST_CREDS, TEST_USERS_CREDS, UserData


@fixture(autouse=True, scope="module")
def set_password_hasher():
    with patch("services.user_service.ph", PasswordHasher.from_parameters(CHEAPEST)):
        yield None


SignUp = Callable[[UserCredentials], Response]


@fixture
def signup(client: TestClient) -> SignUp:
    def f(creds: UserCredentials):
        return client.post(
            "/auth/signup",
            json=creds.model_dump(),
        )

    return f


Login = Callable[[UserCredentials | None], Response]


@fixture
def login(client: TestClient) -> Login:
    def f(creds: UserCredentials | None):
        if creds is None:
            payload = {}
        else:
            payload = creds.model_dump()

        return client.post(
            "/auth/login",
            json=payload,
        )

    return f


async def test_signup_does_not_fail(signup: SignUp):
    response = signup(TEST_CREDS)
    assert response.status_code == status.HTTP_200_OK


async def test_signup_no_reuse(signup: SignUp):
    response = signup(TEST_CREDS)
    assert response.status_code == status.HTTP_200_OK
    response = signup(TEST_CREDS)
    assert response.status_code == status.HTTP_409_CONFLICT


async def test_signup_can_login(signup: SignUp, login: Login):
    response = signup(TEST_CREDS)
    assert response.status_code == status.HTTP_200_OK
    response = login(TEST_CREDS)
    assert response.status_code == status.HTTP_200_OK


async def test_signup_multiple(signup: SignUp, login: Login):
    for creds in TEST_USERS_CREDS.values():
        _ = signup(creds).raise_for_status()
    for creds in TEST_USERS_CREDS.values():
        _ = login(creds).raise_for_status()


async def test_login_requires_signup(login: Login):
    response = login(TEST_CREDS)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.usefixtures("user_user")
async def test_login_requires_correct_email(login: Login):
    creds = TEST_CREDS.model_copy()
    creds.email = "wrongemail"

    response = login(creds)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.usefixtures("user_user")
async def test_login_requires_correct_password(login: Login):
    creds = TEST_CREDS.model_copy()
    creds.email = "wrongpassword"

    response = login(creds)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def check_provided_token_works(client: TestClient, login: Login, user: UserData):
    response = login(user.creds)
    assert response.status_code == status.HTTP_200_OK
    client.cookies.set("access_token", response.cookies["access_token"])

    response = client.get("/auth/me_myself_and_I")
    assert response.status_code == status.HTTP_200_OK
    info = response.json()
    assert info["role"] == user.role
    assert info["email"] == user.creds.email


async def test_login_provided_token_works(
    client: TestClient, login: Login, user_user: UserData
):
    check_provided_token_works(client, login, user_user)


async def test_info_anon(client: TestClient):
    response = client.get("/auth/me_myself_and_I")
    assert response.status_code == status.HTTP_200_OK
    info = response.json()
    assert info["role"] == "anon"
    assert info["email"] is None
