from typing import Optional, List, Dict, Any
import asyncpg
from supabase import create_client, Client

from core.config import Settings
from core.logging import get_logger
from core.exceptions import DatabaseException

logger = get_logger(__name__)


class DatabaseService:
    def __init__(self, supabase_client: Client, pool: Optional[asyncpg.Pool] = None):
        self.supabase = supabase_client
        self.pool = pool

    @staticmethod
    async def create(settings: Settings) -> "DatabaseService":
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning("Supabase credentials not configured, creating mock database service")
            return DatabaseService(None, None)

        try:
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except Exception as e:
            logger.warning(f"Failed to create Supabase client: {e}. Running with mock database service.")
            supabase = None

        pool = None
        if settings.DATABASE_URL:
            try:
                pool = await asyncpg.create_pool(
                    settings.DATABASE_URL,
                    min_size=1,
                    max_size=settings.DATABASE_POOL_SIZE,
                )
                logger.info(f"Database pool created with size {settings.DATABASE_POOL_SIZE}")
            except Exception as e:
                logger.warning(f"Failed to create database pool: {e}")

        return DatabaseService(supabase, pool)

    async def query(
        self,
        table: str,
        select: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        if not self.supabase:
            logger.warning("Supabase client not available, returning empty result")
            return []
        
        try:
            query_builder = self.supabase.table(table).select(select)

            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        query_builder = query_builder.in_(key, value)
                    else:
                        query_builder = query_builder.eq(key, value)

            result = query_builder.range(offset, offset + limit - 1).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise DatabaseException(f"Query failed on table '{table}'")

    async def get_one(
        self,
        table: str,
        filters: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        try:
            query_builder = self.supabase.table(table).select("*")
            for key, value in filters.items():
                query_builder = query_builder.eq(key, value)

            result = query_builder.single().execute()
            return result.data
        except Exception as e:
            logger.warning(f"Get one failed: {e}")
            return None

    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            result = self.supabase.table(table).insert(data).execute()
            return result.data[0] if result.data else data
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise DatabaseException(f"Insert failed on table '{table}'")

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            query_builder = self.supabase.table(table)
            for key, value in filters.items():
                query_builder = query_builder.eq(key, value)

            result = query_builder.update(data).execute()
            return result.data[0] if result.data else data
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise DatabaseException(f"Update failed on table '{table}'")

    async def upsert(
        self,
        table: str,
        data: Dict[str, Any],
        on_conflict: str = "id",
    ) -> Dict[str, Any]:
        try:
            result = self.supabase.table(table).upsert(
                data,
                on_conflict=on_conflict,
            ).execute()
            return result.data[0] if result.data else data
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            raise DatabaseException(f"Upsert failed on table '{table}'")

    async def delete(
        self,
        table: str,
        filters: Dict[str, Any],
    ) -> None:
        try:
            query_builder = self.supabase.table(table)
            for key, value in filters.items():
                query_builder = query_builder.eq(key, value)

            query_builder.delete().execute()
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise DatabaseException(f"Delete failed on table '{table}'")

    async def rpc(
        self,
        function_name: str,
        params: Dict[str, Any],
    ) -> Any:
        try:
            result = self.supabase.rpc(function_name, params).execute()
            return result.data
        except Exception as e:
            logger.error(f"RPC failed: {e}")
            raise DatabaseException(f"RPC call '{function_name}' failed")

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            logger.info("Closed database pool")

    async def health_check(self) -> bool:
        try:
            result = await self.query("_health_check", limit=1)
            return True
        except Exception:
            return False
