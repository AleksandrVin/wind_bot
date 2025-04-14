"""
Use Case: Add a new weather log entry.
"""

import logging
from typing import Any, Dict

from application.interfaces.weather_log_repository import AbstractWeatherLogRepository
from interfaces.web.models import WeatherLog  # Assuming repo returns ORM model for now

logger = logging.getLogger(__name__)


class AddWeatherLogUseCase:
    def __init__(self, repo: AbstractWeatherLogRepository):
        self.repo = repo

    def execute(self, log_data: Dict[str, Any]) -> WeatherLog:
        """Adds a weather log entry.

        Args:
            log_data: Dictionary containing data for the new log entry.

        Returns:
            The created WeatherLog object.

        Raises:
            Exception: If the repository fails to add the log.
        """
        logger.info(f"Executing AddWeatherLogUseCase with data: {log_data}")
        try:
            # In a stricter setup, log_data might be a Domain Model object
            created_log = self.repo.add_log(log_data)
            return created_log
        except Exception as e:
            logger.error(f"AddWeatherLogUseCase failed: {e}", exc_info=True)
            # Depending on requirements, might handle specific exceptions or just re-raise
            raise
