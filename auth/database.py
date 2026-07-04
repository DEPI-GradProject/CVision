from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings


@lru_cache
def get_async_engine():
    return create_async_engine(settings.database_url_async, echo=False, pool_pre_ping=True)


@lru_cache
def get_async_session_maker():
    engine = get_async_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session():
    async with get_async_session_maker()() as session:
        yield session
