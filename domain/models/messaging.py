"""
Domain models for messaging in the wind sports Telegram bot.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from domain.models.weather import WeatherData


class MessageType(str, Enum):
    """Types of messages the bot can send"""

    CURRENT_WEATHER = "current_weather"
    DAILY_FORECAST = "daily_forecast"
    WIND_ALERT = "wind_alert"
    ERROR = "error"


class BotMessage(BaseModel):
    """Message to be sent by the bot"""

    message_type: MessageType
    weather_data: Optional[WeatherData] = None
    error_message: Optional[str] = None
    chat_id: Optional[int] = None
    language: str = "en"
