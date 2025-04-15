"""
Database connection setup using SQLModel.
Uses settings from config.py.
Provides an engine and a session factory.
"""

import logging

# Use async engine and session
from sqlalchemy.ext.asyncio import create_async_engine  # Import from SQLAlchemy
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel  # create_engine is no longer needed here
from sqlmodel.ext.asyncio.session import AsyncSession  # Correct import for AsyncSession

from config import settings

# Models are no longer imported here; SQLModel handles metadata registration
# when the model classes inheriting from it are defined/imported elsewhere (e.g., in init_db.py).
# from domain.models.stats import BotStats # noqa - REMOVED
# from domain.models.weather import WeatherLog # noqa - REMOVED

logger = logging.getLogger(__name__)

# Create the async engine using SQLAlchemy's function
async_engine = create_async_engine(settings.DATABASE_URI, echo=settings.DEBUG, future=True)

# Create an async session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,  # Use AsyncSession from SQLModel
    expire_on_commit=False,  # Recommended for async use
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Initialize the database by creating tables. Runs asynchronously."""
    logger.info("Initializing database...")
    # Ensure models are imported somewhere before this runs (e.g., in the script calling this)
    # so SQLModel.metadata is populated.
    async with async_engine.begin() as conn:
        try:
            # await conn.run_sync(SQLModel.metadata.drop_all) # Uncomment to drop tables first
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables created successfully (if they didn't exist).")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}", exc_info=True)
            raise


# Dependency for FastAPI or other frameworks (optional here, more relevant in web layer)
# async def get_async_session() -> AsyncSession:
#     async with AsyncSessionLocal() as session:
#         yield session
