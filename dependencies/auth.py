import logging
from datetime import datetime, timezone
from typing import Annotated, Any, Never, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyCookie
from sqlalchemy.future import select

from db.schemas import User

logger = logging.getLogger(__name__)


async def get_request_token(
    cookie_token: Annotated[
        str | None, Depends(APIKeyCookie(name="access_token", auto_error=False))
    ],
) -> str | None:
    if cookie_token:
        return cookie_token
    return None


RequestToken = Annotated[str | None, Depends(get_request_token)]


def token_error(
    tkn: object, message: str, *args: object, detail: str = "Invalid token"
) -> Never:
    logger.warning(message + "\nToken: %s", *args, tkn)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
    )


async def get_current_user(
    token: RequestToken,
    request: Request,
) -> Optional[User]:
    if not token:
        logger.debug("No token provided.")
        return None

    try:
        payload = jwt.decode(token, request.state.jwt_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        token_error(token, "JWT decoding failed")

    ##
    # Optimistic parsing, for the sake of simplicity
    ##

    validate_not_expired(payload)

    user_id = payload["sub"]

    async with request.state.async_session() as session:
        result = await session.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

    if user is None:
        token_error(payload, "User with ID %d not found in DB.", user_id)

    return user


CurrentUser = Annotated[User | None, Depends(get_current_user)]


async def get_user_role(
    current_user: CurrentUser,
) -> str:
    """
    Determines the user's role based on the current_user object.
    Returns 'anon' if no user is authenticated or if authentication fails.
    """
    if current_user is None:
        return "anon"
    return current_user.role


def has_role(allowed_roles: list[str]):
    def role_checker(
        current_user: CurrentUser,
        role: Annotated[str, Depends(get_user_role)],
    ):
        if role in allowed_roles:
            return role
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have any of the required roles: {', '.join(allowed_roles)}. Current role: {role}",
            )

    return role_checker


AnyRole = Annotated[str, Depends(get_user_role)]
AdminRole = Annotated[str, Depends(has_role(["admin"]))]


def validate_not_expired(payload: Any):
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    if exp < now:
        token_error(payload, "token has expired. exp=%s < now=%s", exp, now)
