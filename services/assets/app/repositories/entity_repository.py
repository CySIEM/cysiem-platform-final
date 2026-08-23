from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity
from app.repositories.base import SqlAlchemyRepository


class EntityRepository(SqlAlchemyRepository[Entity]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Entity)
