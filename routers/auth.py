import jwt
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from services.user_service import create_user, authenticate_user
from typing import Dict
from db.schemas import User
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" # TODO: add to environment variable
ALGORITHM = "HS256"

class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.get('/') # TODO: change into something more meaningful.
async def say_schalom():
    return "Schalom, world!"

@router.post("/signup", summary="Register a new user")
async def signup(data: SignupRequest, request: Request):
    """
    Registers a new user with the provided email and password.

    Args:
        data (SignupRequest): Email and password fields
        request (Request): HTTP request object containing async_session 

    Returns:
        dict: Contains user ID and email of the newly registered user
    """
    try:
        async with request.state.async_session() as session: # TODO: (Question) should the async_session be started here?
            user: User = await create_user(session, data.email, data.password)
            print(f"User created: {user}")
            return {"id": str(user.id), "email": user.email}
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        logger.error(f"User registration failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during signup.")
    
@router.post("/login", summary="Authenticate an existing user")
async def login(data: LoginRequest, request: Request) -> Dict[str, str]:
    """
    Verify user credentials and return a JWT token.
 
    Args:
        data (LoginRequest): Email and password
        request (Request): HTTP request object containing async_session

    Returns:
        dict: Success message, JWT access token
    """
    try:
        async with request.state.async_session() as session: # TODO: (Question) should the async_session be started here?
            user: User = await authenticate_user(session, data.email, data.password)

            payload = {
                "sub": str(user.id),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1)
            }

            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return {"message": "Login successful.", "access_token": token}

    except HTTPException as exc:
        raise exc
    except Exception as exc:
        logger.error(f"User login failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during login.")