"""
Celery tasks for the wind sports Telegram bot.
These tasks should primarily instantiate and execute application use cases.
"""

import asyncio
import logging
from datetime import datetime

from celery import Celery
from celery.schedules import crontab

# Import Use Cases
from application.use_cases.process_scheduled_weather_check import ProcessScheduledWeatherCheckUseCase
from application.use_cases.send_daily_forecast import SendDailyForecastUseCase
from celery_app import celery_app
from config import settings
from domain.models.messaging import BotMessage, MessageType

# Import Infrastructure implementations needed for Use Case instantiation
# (Ideally use a Dependency Injection container/factory)
from infrastructure.notifications.telegram_sender import TelegramNotificationService
from infrastructure.persistence.redis_alert_state_repository import RedisAlertStateRepository
from infrastructure.persistence.sql_stats_repository import SqlStatsRepository
from infrastructure.persistence.sql_weather_log_repository import SqlWeatherLogRepository
from infrastructure.weather.openweather_service import OpenWeatherService
from interfaces.telegram.bot_controller import TelegramBotController

# Configure logging
logger = logging.getLogger(__name__)

# Wind alert tracking to prevent duplicate alerts
# Dictionary to track the last alert sent for each chat ID
# Format: {chat_id: date_sent}
wind_alerts_sent = {}

# Initialize services
weather_service = OpenWeatherService(
    api_key=settings.OPENWEATHER_API_KEY, latitude=settings.LATITUDE, longitude=settings.LONGITUDE
)

bot_controller = TelegramBotController(token=settings.TELEGRAM_TOKEN)

# Configure Celery
app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,  # Using Redis for results backend as well
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Allow json content
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# --- Task Definitions --- #


@app.task(name="tasks.check_weather_and_alert")
def check_weather_and_alert():
    """Scheduled task to check weather and potentially send alerts."""
    logger.info("Starting scheduled task: check_weather_and_alert")
    try:
        # Instantiate dependencies for the use case
        weather_service = OpenWeatherService()
        notifier = TelegramNotificationService(token=settings.TELEGRAM_TOKEN)
        alert_repo = RedisAlertStateRepository()

        # Instantiate the use case, injecting repository *classes*
        use_case = ProcessScheduledWeatherCheckUseCase(
            weather_service=weather_service,
            alert_repo=alert_repo,
            notifier=notifier,
            stats_repo_cls=SqlStatsRepository,  # Pass the class
            weather_log_repo_cls=SqlWeatherLogRepository,  # Pass the class
        )

        # Execute the use case - session management is handled within execute
        asyncio.run(use_case.execute())
        logger.info("Finished scheduled task: check_weather_and_alert")

    except Exception as e:
        logger.error(f"Error in scheduled task check_weather_and_alert: {e}", exc_info=True)


@celery_app.task(name="tasks.send_daily_forecast_task")
def send_daily_forecast_task():
    """Scheduled task to send the daily forecast."""
    logger.info("Task send_daily_forecast_task triggered.")
    try:
        # Instantiate dependencies
        notifier = TelegramNotificationService()
        weather_service = OpenWeatherService()

        # Instantiate and execute the use case
        use_case = SendDailyForecastUseCase(notifier, weather_service)
        asyncio.run(use_case.execute())

    except Exception as e:
        logger.error(f"Error in send_daily_forecast_task: {e}", exc_info=True)


@celery_app.task
def send_daily_forecast():
    """Send the daily weather forecast to all allowed chats."""
    logger.info("Sending daily forecast")

    try:
        # Get current weather data for forecast
        weather_data = weather_service.get_current_weather()

        if not weather_data:
            logger.error("Failed to get weather data for daily forecast")
            return

        # Send forecast to all allowed chats
        for chat_id in settings.ALLOWED_CHAT_IDS:
            try:
                # Create message object
                bot_message = BotMessage(
                    message_type=MessageType.DAILY_FORECAST,
                    weather_data=weather_data,
                    chat_id=chat_id,
                    language=settings.DEFAULT_LANGUAGE,
                )

                # Create an event loop for the async send_message
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(bot_controller.send_message(bot_message))
                loop.close()
                logger.info(f"Daily forecast sent to chat {chat_id}")

            except Exception as e:
                logger.error(f"Failed to send daily forecast to chat {chat_id}: {e}")

    except Exception as e:
        logger.error(f"Error sending daily forecast: {e}")


@celery_app.task
def send_wind_alert(weather_data_dict):
    """
    Send a wind alert to all allowed chats.

    Args:
        weather_data_dict: Dictionary representation of WeatherData object
    """
    from domain.models.weather import WeatherData

    logger.info("Processing wind alert")

    try:
        # Convert dictionary back to WeatherData object
        weather_data = WeatherData.parse_obj(weather_data_dict)

        today = datetime.now().date()

        # Send alert to all allowed chats
        for chat_id in settings.ALLOWED_CHAT_IDS:
            # Check if we've already sent an alert to this chat today
            if chat_id in wind_alerts_sent and wind_alerts_sent[chat_id] == today:
                logger.info(f"Skipping wind alert for chat {chat_id}: already sent today")
                continue

            try:
                # Create message object
                bot_message = BotMessage(
                    message_type=MessageType.WIND_ALERT,
                    weather_data=weather_data,
                    chat_id=chat_id,
                    language=settings.DEFAULT_LANGUAGE,
                )

                # Create an event loop for the async send_message
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(bot_controller.send_message(bot_message))
                loop.close()

                # Update tracking
                wind_alerts_sent[chat_id] = today

                logger.info(f"Wind alert sent to chat {chat_id}")

            except Exception as e:
                logger.error(f"Failed to send wind alert to chat {chat_id}: {e}")

    except Exception as e:
        logger.error(f"Error processing wind alert: {e}")


# Define the schedule for the task
app.conf.beat_schedule = {
    "check-weather-every-interval": {
        "task": "tasks.check_weather_and_alert",
        # Schedule based on settings
        "schedule": crontab(minute=f"*/{settings.WEATHER_CHECK_INTERVAL_MINUTES}"),
    },
    # Add other scheduled tasks here if needed
}
