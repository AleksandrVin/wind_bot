"""
Database models for the web interface of the wind sports Telegram bot.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

# Define a base class for SQLAlchemy models
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""
    pass

# Create the SQLAlchemy instance
db = SQLAlchemy(model_class=Base)

class BotStats(db.Model):
    """Statistics about the bot's usage."""
    id = Column(Integer, primary_key=True)
    messages_processed = Column(Integer, default=0)
    weather_commands = Column(Integer, default=0)
    forecast_commands = Column(Integer, default=0)
    wind_commands = Column(Integer, default=0)
    alerts_sent = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.now)


class WeatherLog(db.Model):
    """Log of weather data."""
    id = Column(Integer, primary_key=True)
    temperature = Column(Float)
    wind_speed_knots = Column(Float)
    wind_speed_ms = Column(Float)
    has_rain = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now)