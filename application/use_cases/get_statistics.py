"""
Use Case: Retrieve bot statistics and recent weather logs.
"""

import logging
from typing import List, Optional, Tuple

from application.interfaces.stats_repository import AbstractStatsRepository
from application.interfaces.weather_log_repository import AbstractWeatherLogRepository

# Use cases operate on DTOs/Schemas
from interfaces.web.schemas import BotStatsRead, WeatherLogRead

logger = logging.getLogger(__name__)


class GetStatisticsUseCase:
    def __init__(self, stats_repo: AbstractStatsRepository, weather_repo: AbstractWeatherLogRepository):
        self.stats_repo = stats_repo
        self.weather_repo = weather_repo

    def execute_dashboard(self) -> Tuple[Optional[BotStatsRead], List[WeatherLogRead]]:
        """Retrieves data needed for the main dashboard (index page)."""
        logger.info("Executing GetStatisticsUseCase for dashboard")
        try:
            latest_stats = self.stats_repo.get_latest_stats()
            recent_logs = self.weather_repo.get_recent_logs(hours=24)  # Default 24h for dashboard
            return latest_stats, recent_logs
        except Exception as e:
            logger.error(f"GetStatisticsUseCase (dashboard) failed: {e}", exc_info=True)
            return None, []  # Return empty data on error

    def execute_stats_page(self) -> Tuple[List[BotStatsRead], List[WeatherLogRead]]:
        """Retrieves data needed for the statistics page."""
        logger.info("Executing GetStatisticsUseCase for stats page")
        try:
            all_stats = self.stats_repo.get_all_stats()
            # Maybe get more logs for the stats page, e.g., 7 days
            weather_logs = self.weather_repo.get_recent_logs(hours=24 * 7)
            return all_stats, weather_logs
        except Exception as e:
            logger.error(f"GetStatisticsUseCase (stats page) failed: {e}", exc_info=True)
            return [], []  # Return empty data on error

    def execute_recent_weather(self, hours: int = 24) -> List[WeatherLogRead]:
        """Retrieves recent weather logs for the API endpoint."""
        logger.info(f"Executing GetStatisticsUseCase for recent weather (hours={hours})")
        try:
            return self.weather_repo.get_recent_logs(hours=hours)
        except Exception as e:
            logger.error(f"GetStatisticsUseCase (recent weather) failed: {e}", exc_info=True)
            return []
