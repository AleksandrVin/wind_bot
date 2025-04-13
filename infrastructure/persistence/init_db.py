"""
Database initialization script for PostgreSQL.
This script will create all the necessary tables in the PostgreSQL database.
"""
import logging
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from flask import Flask
from config import settings
from interfaces.web.models import db, BotStats, WeatherLog

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def init_db():
    """Initialize the database schema."""
    logger.info("Initializing database schema...")
    
    # If using SQLite, ensure the directory exists
    if settings.DATABASE_URI.startswith('sqlite:///'):
        db_path = settings.DATABASE_URI.replace('sqlite:///', '')
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Ensured SQLite directory exists: {db_dir}")
    
    # Create a temporary Flask app
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URI
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = settings.DATABASE_ENGINE_OPTIONS
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # If PostgreSQL, check if tables were created
        if settings.DATABASE_URI.startswith('postgresql'):
            try:
                engine = db.engine
                conn = engine.connect()
                tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'").fetchall()
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
