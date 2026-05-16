from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Widget(SQLModel, table=True):
    __tablename__ = "widgets"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(
        index=True,
        max_length=120,
        sa_column_kwargs={"unique": True},
    )
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
