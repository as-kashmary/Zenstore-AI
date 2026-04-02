"""
Shared FastAPI dependencies injected into route handlers.

- get_db:           yields an async SQLAlchemy session
- get_current_user: (added in feature/authentication)
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional async database session.
    Automatically closed when the request finishes.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()