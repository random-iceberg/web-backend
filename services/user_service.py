import logging

from fastapi import HTTPException
from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.schemas import User

logger = logging.getLogger(__name__)


async def create_user(db: AsyncSession, email: str, password: str) -> User:
    existing_user = await db.execute(select(User).where(User.email == email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Duplicate email.")

    hashed_pw = bcrypt.hash(password)
    new_user = User(email=email, hashed_password=hashed_pw)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not bcrypt.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    return user
