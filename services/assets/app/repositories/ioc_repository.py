from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ioc import IOC
from app.repositories.base import SqlAlchemyRepository


class IOCRepository(SqlAlchemyRepository[IOC]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, IOC)
