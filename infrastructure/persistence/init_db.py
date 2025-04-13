"""
Database initialization script for PostgreSQL.
This script will create all the necessary tables in the PostgreSQL database.
"""

import logging
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from flask import Flask

from config import settings
from interfaces.web.models import BotStats, db

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def init_db():
    """Initialize the database schema."""
    logger.info("Initializing database schema...")

    # Adjust SQLite path if needed
    db_uri = settings.DATABASE_URI
    if db_uri.startswith("sqlite:///"):
        # Convert relative path to absolute path
        if not db_uri.startswith("sqlite:////"):  # Not already absolute
            db_path = db_uri.replace("sqlite:///", "")
            # If it's a relative path
            if not os.path.isabs(db_path):
                # Get the absolute path to the project root
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
                abs_db_path = os.path.join(project_root, db_path)
                db_uri = f"sqlite:///{abs_db_path}"
                logger.info(f"Converted SQLite path to absolute: {db_uri}")

        # Ensure the directory exists
        db_path = db_uri.replace("sqlite:///", "")
        db_dir = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Ensured SQLite directory exists: {db_dir}")

    # Create a temporary Flask app
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = settings.DATABASE_ENGINE_OPTIONS
    logger.info(f"Using database URI: {db_uri}")
    db.init_app(app)

    with app.app_context():
        # Create all tables
        db.create_all()

        # If PostgreSQL, check if tables were created
        if settings.DATABASE_URI.startswith("postgresql"):
            try:
                engine = db.engine
                conn = engine.connect()
                tables = conn.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                ).fetchall()
                conn.close()

                if tables:
                    logger.info(f"Created tables: {', '.join([table[0] for table in tables])}")
                else:
                    logger.error("Failed to create database tables in PostgreSQL.")
            except Exception as e:
                logger.error(f"Error checking PostgreSQL tables: {e}")

        # Initialize stats if none exist
        if BotStats.query.count() == 0:
            stats = BotStats()
            db.session.add(stats)
            db.session.commit()
            logger.info("Initialized default bot stats")

        logger.info("Database initialization completed successfully.")

    return True


if __name__ == "__main__":
    init_db()
