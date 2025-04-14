"""
Database session management for SQLAlchemy.
"""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

logger = logging.getLogger(__name__)

# Ensure the directory for SQLite exists if used
if settings.DATABASE_URI.startswith("sqlite:///"):
    db_path = settings.DATABASE_URI.replace("sqlite:///", "")
    db_dir = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(db_dir, exist_ok=True)
    logger.info(f"Ensured SQLite directory exists: {db_dir}")

# Create the SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URI,
    connect_args={"check_same_thread": False} if settings.DATABASE_URI.startswith("sqlite") else {},
    pool_pre_ping=settings.DATABASE_ENGINE_OPTIONS.get("pool_pre_ping", True),
    pool_recycle=settings.DATABASE_ENGINE_OPTIONS.get("pool_recycle", 300),
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()


def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


logger.info(f"Database engine created for URI: {settings.DATABASE_URI}")
