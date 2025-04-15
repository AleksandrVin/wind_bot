"""
Use Case: Generate a formatted weather report message.
"""

import logging
from typing import Optional

from application.utils.message_formatting import format_weather_message
from config import Language
from domain.models.messaging import MessageType

# Use domain models and abstract services
from domain.models.weather import WeatherData
from infrastructure.weather.openweather_service import (
    OpenWeatherService,  # Assuming direct use for now, could abstract later
)

logger = logging.getLogger(__name__)


class GenerateWeatherReportUseCase:
    def __init__(self, weather_service: OpenWeatherService):
        # Ideally, inject AbstractWeatherService, but using concrete for now
        self.weather_service = weather_service

    def execute(self, report_type: MessageType, language: str = Language.ENGLISH) -> Optional[str]:
        """Fetches current weather and formats a report message.

        Args:
            report_type: The type of report (e.g., CURRENT_WEATHER, DAILY_FORECAST).
            language: The language for the report.

        Returns:
            The formatted message string, or None if weather data is unavailable.
        """
        logger.info(f"Generating weather report: type={report_type}, lang={language}")
        try:
            weather_data: Optional[WeatherData] = self.weather_service.get_current_weather()
            if not weather_data:
                logger.warning("Could not retrieve weather data for report.")
                return None

            # Format the message using the utility
            message = format_weather_message(weather_data, report_type, language)
            return message
        except Exception as e:
            logger.error(f"Error generating weather report: {e}", exc_info=True)
            return None
