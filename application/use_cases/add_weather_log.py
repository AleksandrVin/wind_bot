"""
Use Case: Add a new weather log entry.
"""

import logging

from application.interfaces.weather_log_repository import AbstractWeatherLogRepository

# Use cases now operate on DTOs/Schemas
from interfaces.web.schemas import WeatherLogCreate, WeatherLogRead

logger = logging.getLogger(__name__)


class AddWeatherLogUseCase:
    def __init__(self, repo: AbstractWeatherLogRepository):
        self.repo = repo

    def execute(self, log_data: WeatherLogCreate) -> WeatherLogRead:
        """Adds a weather log entry.

        Args:
            log_data: Pydantic model containing data for the new log entry.

        Returns:
            The created WeatherLog DTO.

        Raises:
            Exception: If the repository fails to add the log.
        """
        logger.info(f"Executing AddWeatherLogUseCase with data: {log_data}")
        try:
            created_log_dto = self.repo.add_log(log_data)
            return created_log_dto
        except Exception as e:
            logger.error(f"AddWeatherLogUseCase failed: {e}", exc_info=True)
            raise
