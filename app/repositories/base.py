"""
Generic async CRUD repository.

Every domain repository (UserRepository, ProductRepository, …)
inherits from `BaseRepository` and gets these operations for free.
Domain repos can override or extend with owner-scoped queries, etc.
"""

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_class import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Thin async wrapper around common SQLAlchemy operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    # ── Read ─────────────────────────────────────────────

    async def get(self, id: str) -> Optional[ModelType]:
        """Return a single row by primary key, or None."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """Return a paginated list of rows."""
        result = await self.session.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return total row count for the model's table."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    # ── Create ───────────────────────────────────────────

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        Insert a new row.

        `obj_in` is a plain dict (typically `schema.model_dump()`).
        The `id` field is auto-generated if not provided.
        """
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    # ── Update ───────────────────────────────────────────

    async def update(
        self,
        id: str,
        obj_in: Dict[str, Any],
    ) -> Optional[ModelType]:
        """
        Patch an existing row.  Only keys present in `obj_in` are updated.
        Returns None if the row doesn't exist.
        """
        db_obj = await self.get(id)
        if db_obj is None:
            return None

        for key, value in obj_in.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    # ── Delete ───────────────────────────────────────────

    async def delete(self, id: str) -> bool:
        """
        Delete a row by primary key.
        Returns True if deleted, False if not found.
        """
        db_obj = await self.get(id)
        if db_obj is None:
            return False

        await self.session.delete(db_obj)
        await self.session.commit()
        return True