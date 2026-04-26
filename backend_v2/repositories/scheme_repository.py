from typing import List, Dict, Any

from core.logging import get_logger
from services.database_service import DatabaseService

logger = get_logger(__name__)


class SchemeRepository:
    def __init__(self, db: DatabaseService):
        self.db = db

    async def search(
        self,
        query: str,
        state: str = None,
        category: str = "agriculture",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        try:
            filters = {"category": category}
            if state:
                filters["state"] = state

            schemes = await self.db.query(
                "schemes",
                filters=filters,
                limit=limit,
            )
            return schemes
        except Exception as e:
            logger.error(f"Failed to search schemes: {e}")
            return []

    async def get_by_id(self, scheme_id: str) -> Dict[str, Any]:
        try:
            return await self.db.get_one("schemes", {"id": scheme_id})
        except Exception as e:
            logger.error(f"Failed to get scheme: {e}")
            return None

    async def get_all_states(self) -> List[str]:
        try:
            result = await self.db.query(
                "schemes",
                select="state",
                limit=1000,
            )
            states = list(set(s.get("state") for s in result if s.get("state")))
            return sorted(states)
        except Exception as e:
            logger.error(f"Failed to get states: {e}")
            return []

    async def vector_search(
        self,
        embedding: List[float],
        state: str = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        try:
            params = {
                "query_embedding": embedding,
                "match_threshold": 0.72,
                "match_count": limit,
                "filter_state": state.lower() if state else "",
                "filter_category": "agriculture",
            }
            return await self.db.rpc("match_schemes", params)
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
