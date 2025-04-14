"""
Celery tasks for the wind sports Telegram bot.
"""

import asyncio
import logging
from datetime import datetime

from application.utils.weather_utils import should_send_wind_alert
from celery_app import celery_app
from config import settings
from domain.models.messaging import BotMessage, MessageType
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


@celery_app.task
def check_weather():
    """
    Check the current weather conditions and send alerts if wind speed
    exceeds the threshold.
    """
    logger.info("Checking weather conditions for wind alerts")

    try:
        # Get current weather data
        weather_data = weather_service.get_current_weather()

        if not weather_data:
            logger.error("Failed to get current weather data")
            return

        # Determine if we should send a wind alert
        if should_send_wind_alert(weather_data):
            logger.info(f"Wind alert condition met: {weather_data.wind.speed_knots} knots")
            # Directly call the send_wind_alert task
            send_wind_alert(weather_data.dict())
        else:
            logger.info(f"No wind alert needed. Current wind: {weather_data.wind.speed_knots} knots")

    except Exception as e:
        logger.error(f"Error checking weather: {e}")


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
