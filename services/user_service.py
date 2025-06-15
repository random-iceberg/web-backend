import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.schemas import User

logger = logging.getLogger(__name__)

ph = PasswordHasher()


async def create_user(
    db: AsyncSession, email: str, password: str, role: str = "user"
) -> User:
    existing_user = await db.execute(select(User).where(User.email == email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Duplicate email.")

    hashed_pw = ph.hash(password)
    new_user = User(email=email, hashed_password=hashed_pw, role=role)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    try:
        ph.verify(user.hashed_password, password)
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    return user
