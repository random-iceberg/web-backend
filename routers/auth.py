import logging

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from db.schemas import User
from dependencies.auth import CurrentUser
from dependencies.state import RequestState
from services.user_service import authenticate_user, create_user, mk_jwt_token

logger = logging.getLogger(__name__)
router = APIRouter()


class SignupRequest(BaseModel):
    email: str
    password: str


class SignupResponse(BaseModel):
    email: str
    message: str = "User registered successfully."


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    message: str = "Login successful."


class InfoResponse(BaseModel):
    email: str | None
    role: str


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
        return SignupResponse(email=user.email)


@router.post("/login", summary="Generate an access token")
async def login(
    data: LoginRequest, state: RequestState, response: Response
) -> LoginResponse:
    """
    Verify user credentials and return a JWT token.
    """

    async with state.async_session() as session:
        user: User = await authenticate_user(session, data.email, data.password)

    token = mk_jwt_token(user=user, jwt_key=state.jwt_key)

    response.set_cookie(
        key="access_token",
        value=token,
        # max_age=max_age.seconds, session cookie for now
        httponly=True,
        samesite="strict",
    )
    return LoginResponse()


@router.post("/logout")
async def logout(response: Response) -> None:
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="strict",
    )


@router.get("/me_myself_and_I", summary="Get user info")
async def get_info(user: CurrentUser) -> InfoResponse:
    if user is None:
        return InfoResponse(email=None, role="anon")
    return InfoResponse(email=user.email, role=user.role)
