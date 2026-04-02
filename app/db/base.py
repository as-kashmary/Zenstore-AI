"""
Async SQLAlchemy engine, session factory, and table initialisation.

Uses the aiomysql driver for fully async MySQL access.
`init_db()` is called once at startup to issue CREATE TABLE IF NOT EXISTS
for every model registered with `Base.metadata`.
"""

import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.db.base_class import Base

logger = logging.getLogger("zenstore.db")

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.APP_ENV == "development"),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """
    Import every ORM model so it registers with `Base.metadata`,
    then issue CREATE TABLE for any that don't yet exist.
    """
    # ── Force model imports so metadata knows about them ──

    logger.info("Running Base.metadata.create_all …")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("create_all complete.")