"""
Database initialization script.
This script will create all the necessary tables based on SQLAlchemy models.
"""

import logging
import os
import sys
from time import sleep
from sqlalchemy.exc import OperationalError
from infrastructure.persistence.database import Base, SessionLocal, engine

# Import models to ensure they are registered with Base
from interfaces.web.models import BotStats

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds

def init_db():
    """Initialize the database schema."""
    logger.info("Attempting to initialize database schema...")

    for attempt in range(MAX_RETRIES):
        try:
            # Create all tables defined in models imported above
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully (if they didn't exist).")

            # Optionally initialize default data
            db = SessionLocal()
            try:
                if db.query(BotStats).count() == 0:
                    stats = BotStats()
                    db.add(stats)
                    db.commit()
                    logger.info("Initialized default bot stats.")
            finally:
                db.close()

            logger.info("Database initialization completed.")
            return True

        except OperationalError as e:
            logger.warning(f"Database connection failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt + 1 == MAX_RETRIES:
                logger.error("Max retries reached. Failed to connect to the database.")
                raise
            logger.info(f"Retrying in {RETRY_DELAY} seconds...")
            sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"An unexpected error occurred during database initialization: {e}")
            raise

    return False


if __name__ == "__main__":
    if not init_db():
        sys.exit(1)
