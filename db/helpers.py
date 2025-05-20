from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from asyncpg.exceptions import CannotConnectNowError

from .schemas import Base, Feature, Prediction


async def init_db(engine: AsyncEngine):
    # TODO: surely, there should be a better way to wait until database is up
    connected = False
    while not connected:
        try:
            connected = True
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except ConnectionRefusedError:
            connected = False
        except CannotConnectNowError:
            connected = False

    return async_sessionmaker(engine, expire_on_commit=False)


async def populate_features(async_session: async_sessionmaker[AsyncSession]):
    """Ensure that `feature` table is initialized"""

    async with async_session() as session:
        for feature in [
            "pclass",
            "sex",
            "age",
            "sibsp",
            "parch",
            "fare",
            "embarked",
            "title",
        ]:
            _ = await session.execute(
                insert(Feature).values(name=feature).on_conflict_do_nothing()
            )
        await session.commit()
