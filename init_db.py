"""
Script to initialize the database.
Creates tables based on SQLModel definitions.
Can be run manually or as part of deployment.
"""

import asyncio  # Import asyncio
import logging

# Ensure models are imported before initializing DB
# This allows SQLModel to register them.
from infrastructure.persistence.database import (
    async_engine,
    init_db,
)  # Import async init_db and engine

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Async main function to initialize the database."""
    logger.info("Starting database initialization script...")
    try:
        await init_db()  # Await the async function
        logger.info("Database initialization script finished successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
    finally:
        # Gracefully close the engine connection pool
        await async_engine.dispose()
        logger.info("Database engine disposed.")


if __name__ == "__main__":
    asyncio.run(main())  # Run the async main function
