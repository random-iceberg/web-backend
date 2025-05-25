import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Request
from pydantic import BaseModel

from db.schemas import User
from services.user_service import authenticate_user, create_user

logger = logging.getLogger(__name__)
router = APIRouter()


class SignupRequest(BaseModel):
    email: str
    password: str


class SignupResponse(BaseModel):
    id: str
    email: str
    message: str = "User registered successfully."


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    message: str = "Login successful."
    access_token: str


@router.post("/signup", summary="Register a new user")
async def signup(data: SignupRequest, request: Request) -> SignupResponse:
    """
    Registers a new user with the provided email and password.

    Args:
        data (SignupRequest): Email and password fields
        request (Request): HTTP request object containing async_session

    Returns:
        dict: Contains user ID and email of the newly registered user
    """
    async with request.state.async_session() as session:
        user: User = await create_user(session, data.email, data.password)
        return SignupResponse(id=user.id, email=user.email)


@router.post("/login", summary="Authenticate an existing user")
async def login(data: LoginRequest, request: Request) -> LoginResponse:
    """
    Verify user credentials and return a JWT token.

    Args:
        data (LoginRequest): Email and password
        request (Request): HTTP request object containing async_session

    Returns:
        dict: Success message, JWT access token
    """
    async with (
        request.state.async_session() as session
    ):  # TODO: (Question) should the async_session be started here?
        user: User = await authenticate_user(session, data.email, data.password)

        payload = {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        token = jwt.encode(payload, request.state.jwt_key, algorithm="HS256")
        return LoginResponse(access_token=token)
