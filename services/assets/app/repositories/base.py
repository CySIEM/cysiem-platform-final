"""Generic async repository pattern shared by all Layer 3 persistence.

SqlAlchemyRepository[T] wraps common CRUD against a single ORM model.
InMemoryRepository[T] is a drop-in substitute used in unit tests / local
dev without a database.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class SqlAlchemyRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: Type[ModelT]):
        self.session = session
        self.model = model

    async def get(self, id_: uuid.UUID) -> Optional[ModelT]:
        return await self.session.get(self.model, id_)

    async def list(self, limit: int = 100, offset: int = 0, **filters: Any) -> List[ModelT]:
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))

    async def create(self, **data: Any) -> ModelT:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id_: uuid.UUID, **data: Any) -> Optional[ModelT]:
        instance = await self.get(id_)
        if instance is None:
            return None
        for field, value in data.items():
            setattr(instance, field, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id_: uuid.UUID) -> bool:
        instance = await self.get(id_)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def find_one(self, **filters: Any) -> Optional[ModelT]:
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalars().first()


class InMemoryRepository(Generic[ModelT]):
    """Non-persistent repository for tests / local experimentation."""

    def __init__(self, model: Type[ModelT]):
        self.model = model
        self._store: Dict[uuid.UUID, ModelT] = {}

    async def get(self, id_: uuid.UUID) -> Optional[ModelT]:
        return self._store.get(id_)

    async def list(self, limit: int = 100, offset: int = 0, **filters: Any) -> List[ModelT]:
        items = list(self._store.values())
        for field, value in filters.items():
            items = [i for i in items if getattr(i, field, None) == value]
        return items[offset : offset + limit]

    async def count(self, **filters: Any) -> int:
        return len(await self.list(limit=10_000, **filters))

    async def create(self, **data: Any) -> ModelT:
        instance = self.model(**data)
        if not getattr(instance, "id", None):
            instance.id = uuid.uuid4()
        self._store[instance.id] = instance
        return instance

    async def update(self, id_: uuid.UUID, **data: Any) -> Optional[ModelT]:
        instance = self._store.get(id_)
        if instance is None:
            return None
        for field, value in data.items():
            setattr(instance, field, value)
        return instance

    async def delete(self, id_: uuid.UUID) -> bool:
        return self._store.pop(id_, None) is not None

    async def find_one(self, **filters: Any) -> Optional[ModelT]:
        results = await self.list(limit=1, **filters)
        return results[0] if results else None
