import logging
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.future import select

from db.schemas import User

logger = logging.getLogger(__name__)


# Use HTTPBearer for simple Bearer token authentication
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(http_bearer)], 
    request: Request
) -> Optional[User]:
    if credentials is None:
        logger.debug("No credentials provided.")
        return None
    
    token = credentials.credentials
    if not token:
        logger.debug("No token provided.")
        return None

    try:
        payload = jwt.decode(token, request.state.jwt_key, algorithms=["HS256"])
        user_id: Optional[str] = payload.get("sub")
        token_data_role: Optional[str] = payload.get("role")

        if user_id is None or token_data_role is None:
            logger.warning("Token payload missing user_id or role.")
            return None

    except jwt.PyJWTError:
        logger.warning("Invalid JWT token.")
        return None

    async with request.state.async_session() as session:
        result = await session.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning(f"User with ID {user_id} not found in DB.")
            return None

        if user.role != token_data_role:
            logger.warning(
                f"User {user.id} role mismatch: token={token_data_role}, db={user.role}."
            )
            return None

        return user


async def get_user_role(
    current_user: Annotated[Optional[User], Depends(get_current_user)],
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
        role: Annotated[str, Depends(get_user_role)],
    ):
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have any of the required roles: {', '.join(allowed_roles)}. Current role: {role}",
            )
        return role

    return role_checker


AnyRole = Annotated[str, Depends(get_user_role)]
AdminRole = Annotated[str, Depends(has_role(["admin"]))]
