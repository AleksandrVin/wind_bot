"""
Celery app configuration for the wind sports Telegram bot.
"""

import os
from celery import Celery
from celery.schedules import crontab

from config import settings

# Create the Celery app with an in-memory broker
celery_app = Celery("tq_wind_bot", broker="memory://", backend="memory://")

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Set up periodic tasks
celery_app.conf.beat_schedule = {
    "check-weather-every-10-minutes": {
        "task": "tasks.check_weather",
        "schedule": settings.WEATHER_CHECK_INTERVAL_MINUTES * 60,  # Convert minutes to seconds
    },
    "send-daily-forecast": {
        "task": "tasks.send_daily_forecast",
        "schedule": crontab(hour=settings.FORECAST_TIME.hour, minute=settings.FORECAST_TIME.minute),
    },
}

if __name__ == "__main__":
    celery_app.start()
