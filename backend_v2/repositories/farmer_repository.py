from typing import Optional, List
from datetime import datetime

from core.logging import get_logger
from core.domain import FarmerProfile, GeoLocation, LanguageCode, CropType
from services.database_service import DatabaseService

logger = get_logger(__name__)


class FarmerRepository:
    def __init__(self, db: DatabaseService):
        self.db = db

    async def get_by_user_id(self, user_id: str) -> Optional[FarmerProfile]:
        try:
            data = await self.db.get_one("farmer_profiles", {"user_id": user_id})
            if not data:
                return None
            return FarmerProfile(**data)
        except Exception as e:
            logger.error(f"Failed to get farmer: {e}")
            return None

    async def create(self, profile: FarmerProfile) -> FarmerProfile:
        try:
            data = profile.to_dict()
            result = await self.db.insert("farmer_profiles", data)
            return FarmerProfile(**result)
        except Exception as e:
            logger.error(f"Failed to create farmer: {e}")
            raise

    async def update(self, profile: FarmerProfile) -> FarmerProfile:
        try:
            profile.updated_at = datetime.utcnow()
            data = profile.to_dict()
            result = await self.db.update(
                "farmer_profiles",
                data,
                {"user_id": profile.user_id},
            )
            return FarmerProfile(**result)
        except Exception as e:
            logger.error(f"Failed to update farmer: {e}")
            raise

    async def upsert(self, profile: FarmerProfile) -> FarmerProfile:
        try:
            profile.updated_at = datetime.utcnow()
            data = profile.to_dict()
            result = await self.db.upsert(
                "farmer_profiles",
                data,
                on_conflict="user_id",
            )
            return FarmerProfile(**result[0]) if result else profile
        except Exception as e:
            logger.error(f"Failed to upsert farmer: {e}")
            raise

    async def delete(self, user_id: str) -> None:
        try:
            await self.db.delete("farmer_profiles", {"user_id": user_id})
        except Exception as e:
            logger.error(f"Failed to delete farmer: {e}")
            raise
