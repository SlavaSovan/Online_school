from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    pass


def get_engine():
    return create_async_engine(settings.DATABASE.database_url)


engine = None
async_session_maker = None


def init_db():
    global engine, async_session_maker

    engine = get_engine()
    async_session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def get_db():
    async with async_session_maker() as session:
        yield session


async def close_db():
    await engine.dispose()
