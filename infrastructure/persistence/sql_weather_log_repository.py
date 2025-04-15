"""
SQLAlchemy implementation of the Weather Log Repository.
Uses SQLModel for models and session management.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession  # Import AsyncSession

from application.interfaces.weather_log_repository import AbstractWeatherLogRepository
from domain.models.weather import WeatherLog
from interfaces.web.schemas import WeatherLogCreate, WeatherLogRead  # Import Schemas

logger = logging.getLogger(__name__)


class SqlWeatherLogRepository(AbstractWeatherLogRepository):
    """SQLAlchemy repository for weather logs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_read_dto(self, orm_obj: WeatherLog) -> WeatherLogRead:
        """Maps ORM object to Read DTO."""
        return WeatherLogRead.from_orm(orm_obj)

    async def add_log(self, log_data: WeatherLogCreate) -> Optional[WeatherLogRead]:
        """Adds a new weather log entry asynchronously."""
        try:
            db_log = WeatherLog.model_validate(log_data)  # Create model instance from DTO
            db_log.timestamp = datetime.utcnow()  # Ensure timestamp is set

            self.session.add(db_log)
            await self.session.commit()
            await self.session.refresh(db_log)
            logger.info(f"Added weather log entry: {db_log.id}")
            return WeatherLogRead.from_orm(db_log)
        except Exception as e:
            logger.error(f"Error adding weather log: {e}", exc_info=True)
            await self.session.rollback()
            return None

    async def get_logs(self, limit: int = 100) -> List[WeatherLogRead]:
        """Retrieves recent weather log entries asynchronously."""
        try:
            statement = select(WeatherLog).order_by(WeatherLog.timestamp.desc()).limit(limit)
            results = await self.session.exec(statement)
            db_logs = results.all()
            return [WeatherLogRead.from_orm(log) for log in db_logs]
        except Exception as e:
            logger.error(f"Error retrieving weather logs: {e}", exc_info=True)
            return []
