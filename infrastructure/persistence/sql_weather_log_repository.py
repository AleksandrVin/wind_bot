"""
SQLAlchemy implementation of the Weather Log repository.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from application.interfaces.weather_log_repository import AbstractWeatherLogRepository
from interfaces.web.models import WeatherLog  # Using the ORM model

logger = logging.getLogger(__name__)


class SqlWeatherLogRepository(AbstractWeatherLogRepository):
    """SQLAlchemy implementation for weather log persistence."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def add_log(self, log_data: Dict[str, Any]) -> WeatherLog:
        try:
            db_log = WeatherLog(**log_data)
            self.db.add(db_log)
            self.db.commit()
            self.db.refresh(db_log)
            logger.info(f"Successfully added weather log record ID: {db_log.id}")
            return db_log
        except Exception as e:
            logger.error(f"Error adding weather log: {e}", exc_info=True)
            self.db.rollback()
            raise  # Re-raise

    def get_recent_logs(self, hours: int = 24) -> List[WeatherLog]:
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
            logs = (
                self.db.query(WeatherLog)
                .filter(WeatherLog.timestamp >= time_threshold)
                .order_by(WeatherLog.timestamp.asc())
                .all()
            )
            return logs
        except Exception as e:
            logger.error(f"Error fetching recent weather logs: {e}", exc_info=True)
            return []
