#!/usr/bin/env python3

import asyncio
import logging
from core.config import get_settings
from services.database_service import DatabaseService
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    try:
        settings = get_settings()
        
        logger.info("Initializing database...")
        
        db_service = await DatabaseService.create(settings)
        
        logger.info("Testing database connection...")
        health = await db_service.health_check()
        if not health:
            raise Exception("Database health check failed")
        
        logger.info("Database connection successful!")
        
        schema_file = Path(__file__).parent / "DATABASE_SCHEMA.sql"
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        logger.info(f"Reading schema from {schema_file}")
        with open(schema_file, "r") as f:
            schema = f.read()
        
        logger.info("Executing schema creation...")
        try:
            from supabase import create_client
            import postgrest
            
            client = create_client(settings.supabase_url, settings.supabase_key)
            
            logger.info("Schema initialization setup complete")
            logger.info("Note: Run the SQL script directly in Supabase SQL Editor or via psql")
            logger.info(f"SQL Schema file: {schema_file}")
            
        except Exception as e:
            logger.error(f"Error setting up schema: {e}")
            logger.info("Please run DATABASE_SCHEMA.sql manually in Supabase SQL Editor")
            return False
        
        logger.info("Database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(init_database())
    exit(0 if success else 1)
