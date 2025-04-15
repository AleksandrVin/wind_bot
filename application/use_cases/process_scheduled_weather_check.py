"""
Use Case: Process Scheduled Weather Check

Orchestrates the process of checking weather conditions,
determining if alerts need to be sent based on thresholds and cooldowns,
sending notifications, and logging relevant data.
Uses manual session management for database operations within the use case.
"""

import logging
from datetime import datetime, timedelta
from typing import Type

from application.interfaces.alert_state_repository import AbstractAlertStateRepository
from application.interfaces.notification_service import AbstractNotificationService
from application.interfaces.stats_repository import AbstractStatsRepository
from application.interfaces.weather_log_repository import AbstractWeatherLogRepository

# Interfaces
from application.interfaces.weather_service import AbstractWeatherService
from config import settings
from domain.models.messaging import MessageType
from domain.models.weather import WeatherData

# Infrastructure (for session management)
from infrastructure.persistence.database import AsyncSessionLocal  # Use Async Session

# DTOs
from interfaces.web.schemas import BotStatsUpdate, WeatherLogCreate

logger = logging.getLogger(__name__)


class ProcessScheduledWeatherCheckUseCase:
    """
    Handles the scheduled weather check, alert logic, notifications, and logging.
    Injects repository *classes* to allow for session management within the use case.
    """

    def __init__(
        self,
        weather_service: AbstractWeatherService,
        alert_repo: AbstractAlertStateRepository,
        notifier: AbstractNotificationService,
        stats_repo_cls: Type[AbstractStatsRepository],  # Class for stats repo
        weather_log_repo_cls: Type[AbstractWeatherLogRepository],  # Class for log repo
    ):
        self.weather_service = weather_service
        self.alert_repo = alert_repo
        self.notifier = notifier
        self.StatsRepository = stats_repo_cls
        self.WeatherLogRepository = weather_log_repo_cls

    async def execute(self) -> None:
        """Executes the scheduled weather check process asynchronously."""
        logger.info("Executing ProcessScheduledWeatherCheckUseCase...")
        session = None  # Initialize session variable
        try:
            # 1. Fetch current weather data
            weather_data = self.weather_service.get_current_weather()
            if not weather_data:
                logger.warning("No weather data received from service.")
                return  # Cannot proceed without data

            # 2. Log weather data and stats (within an async session)
            async with AsyncSessionLocal() as session:
                stats_repo = self.StatsRepository(session)
                weather_log_repo = self.WeatherLogRepository(session)

                # Log weather data
                log_dto = WeatherLogCreate(
                    temperature=weather_data.temperature,
                    wind_speed_knots=weather_data.wind.speed_knots,
                    wind_speed_ms=weather_data.wind.speed_ms,
                    has_rain=bool(weather_data.rain_1h or weather_data.rain_3h),
                )
                await weather_log_repo.add_log(log_dto)
                logger.debug("Weather data logged.")

                # Log stats (e.g., a scheduled check occurred)
                stats_data = BotStatsUpdate(scheduled_checks=1)
                await stats_repo.update_or_create_stats(stats_data)
                logger.debug("Scheduled check stat logged.")

            # --- Alerting Logic --- #
            # 3. Check if wind speed exceeds threshold
            wind_kph = weather_data.wind.speed_knots  # Assuming knots for threshold
            if wind_kph >= settings.WIND_SPEED_ALERT_THRESHOLD_KNOTS:
                logger.info(
                    f"Wind speed {wind_kph:.1f} knots exceeds threshold ({settings.WIND_SPEED_ALERT_THRESHOLD_KNOTS} knots). Checking alert cooldown."
                )
                # 4. Check cooldown and send alerts for each allowed chat ID
                for chat_id in settings.ALLOWED_CHAT_IDS:
                    await self._check_and_send_alert(chat_id, weather_data)
            else:
                logger.info(f"Wind speed {wind_kph:.1f} knots below threshold.")

            logger.info("ProcessScheduledWeatherCheckUseCase finished successfully.")

        except Exception as e:
            logger.error(f"Error during scheduled weather check: {e}", exc_info=True)
            # No explicit rollback needed here if session context manager handles it
            # But good to log the failure

        # Session is automatically closed by the 'async with' block

    async def _check_and_send_alert(self, chat_id: int, weather_data: WeatherData) -> None:
        """Checks cooldown for a chat ID and sends alert if necessary."""
        now = datetime.utcnow()
        cooldown_duration = timedelta(minutes=settings.ALERT_COOLDOWN_MINUTES)

        try:
            last_alert_time_str = self.alert_repo.get_last_alert_timestamp(chat_id)

            if last_alert_time_str:
                last_alert_time = datetime.fromisoformat(last_alert_time_str)
                if now < last_alert_time + cooldown_duration:
                    logger.info(f"Alert cooldown active for chat {chat_id}. Skipping.")
                    return  # Still in cooldown

            # Cooldown passed or no previous alert, send notification
            logger.info(f"Sending wind alert to chat {chat_id}...")
            await self.notifier.send_message(
                chat_id=chat_id,
                message_type=MessageType.WIND_ALERT,
                weather_data=weather_data,
                language=settings.DEFAULT_LANGUAGE,  # Or get specific language if stored
            )

            # Update last alert timestamp in repository
            self.alert_repo.set_last_alert_timestamp(chat_id, now.isoformat())
            logger.info(f"Alert sent and timestamp updated for chat {chat_id}.")

        except Exception as e:
            logger.error(
                f"Failed to process or send alert for chat {chat_id}: {e}",
                exc_info=True,
            )
