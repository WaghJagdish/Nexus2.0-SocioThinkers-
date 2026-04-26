from typing import List, Dict, Any
from datetime import datetime

from core.logging import get_logger
from services.database_service import DatabaseService

logger = get_logger(__name__)


class InteractionRepository:
    def __init__(self, db: DatabaseService):
        self.db = db

    async def create(
        self,
        user_id: str,
        session_id: str,
        query_text: str,
        response_text: str,
        agent_used: str,
    ) -> Dict[str, Any]:
        try:
            data = {
                "user_id": user_id,
                "session_id": session_id,
                "query": query_text,
                "response": response_text,
                "agent_used": agent_used,
                "created_at": datetime.utcnow().isoformat(),
            }
            result = await self.db.insert("interaction_logs", data)
            return result
        except Exception as e:
            logger.error(f"Failed to create interaction log: {e}")
            raise

    async def get_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        try:
            return await self.db.query(
                "interaction_logs",
                filters={"session_id": session_id},
            )
        except Exception as e:
            logger.error(f"Failed to get interactions: {e}")
            return []

    async def get_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            return await self.db.query(
                "interaction_logs",
                filters={"user_id": user_id},
                limit=limit,
            )
        except Exception as e:
            logger.error(f"Failed to get user interactions: {e}")
            return []
