"""
Abstract interface for accessing Weather Log data.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from interfaces.web.models import WeatherLog


class AbstractWeatherLogRepository(ABC):
    """Abstract base class for weather log repositories."""

    @abstractmethod
    def add_log(self, log_data: Dict[str, Any]) -> WeatherLog:
        """Add a new weather log entry.

        Args:
            log_data: Dictionary containing weather log data.

        Returns:
            The newly created WeatherLog record.
        """
        pass

    @abstractmethod
    def get_recent_logs(self, hours: int = 24) -> List[WeatherLog]:
        """Retrieve recent weather logs.

        Args:
            hours: The number of past hours to retrieve logs for.

        Returns:
            A list of WeatherLog records within the time window.
        """
        pass
