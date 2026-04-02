"""
Declarative base and abstract base model.

Every ORM model inherits from `BaseModel`, which provides:
  - id         VARCHAR(36)  primary key  (Python-generated UUID4)
  - created_at DATETIME     server-default NOW()

MySQL has no native UUID type, so we store UUIDs as VARCHAR(36).
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 2.x declarative base."""
    pass


class BaseModel(Base):
    """Abstract base with common columns shared by every table."""

    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )