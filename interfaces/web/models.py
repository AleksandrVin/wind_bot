"""
Database models for the web interface of the wind sports Telegram bot.
Using SQLAlchemy ORM.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer

from infrastructure.persistence.database import Base  # Import Base from the new database setup


class BotStats(Base):
    """Statistics about the bot's usage."""

    __tablename__ = "bot_stats"

    id = Column(Integer, primary_key=True)
    messages_processed = Column(Integer, default=0)
    weather_commands = Column(Integer, default=0)
    forecast_commands = Column(Integer, default=0)
    alerts_sent = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class WeatherLog(Base):
    """Log of weather data."""

    __tablename__ = "weather_log"

    id = Column(Integer, primary_key=True)
    temperature = Column(Float)
    wind_speed_knots = Column(Float)
    wind_speed_ms = Column(Float)
    has_rain = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now)
