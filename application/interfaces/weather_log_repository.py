"""
Abstract interface for accessing Weather Log data.
"""

from abc import ABC, abstractmethod
from typing import List

# Use Pydantic schemas for data transfer
from interfaces.web.schemas import WeatherLogCreate, WeatherLogRead


class AbstractWeatherLogRepository(ABC):
    """Abstract base class for weather log repositories."""

    @abstractmethod
    def add_log(self, log_data: WeatherLogCreate) -> WeatherLogRead:
        """Add a new weather log entry.

        Args:
            log_data: Pydantic model containing weather log data.

        Returns:
            The newly created WeatherLog record as a DTO.
        """
        pass

    @abstractmethod
    def get_recent_logs(self, hours: int = 24) -> List[WeatherLogRead]:
        """Retrieve recent weather logs.

        Args:
            hours: The number of past hours to retrieve logs for.

        Returns:
            A list of WeatherLog records as DTOs within the time window.
        """
        pass
