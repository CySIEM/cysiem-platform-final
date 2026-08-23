from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.repositories.base import SqlAlchemyRepository


class AssetRepository(SqlAlchemyRepository[Asset]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Asset)
