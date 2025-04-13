"""
Configuration settings for the wind sports Telegram bot.
Uses Pydantic for settings management.
"""
from datetime import time
from enum import Enum
from typing import Optional, List, Dict, Any
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Language(str, Enum):
    ENGLISH = "en"
    RUSSIAN = "ru"


class Settings(BaseSettings):
    # Telegram Bot Settings
    TELEGRAM_TOKEN: str = Field(..., description="Telegram Bot API token")
    ALLOWED_CHAT_IDS: List[int] = Field(
        default_factory=list,
        description="List of chat IDs where the bot is allowed to operate"
    )
    ADMIN_USER_IDS: List[int] = Field(
        default_factory=list,
        description="List of user IDs that have admin privileges"
    )
    
    # Weather API Settings
    OPENWEATHER_API_KEY: str = Field(..., description="OpenWeather API key")
    LATITUDE: float = Field(12.360176, description="Default location latitude")
    LONGITUDE: float = Field(99.996044, description="Default location longitude")
    
    # Wind Speed Threshold Settings
    WIND_THRESHOLD_KNOTS: float = Field(15.0, description="Wind speed threshold in knots for alerts")
    
    # Language Settings
    DEFAULT_LANGUAGE: Language = Field(Language.ENGLISH, description="Default language for bot responses")
    
    # Timing Settings
    WEATHER_CHECK_INTERVAL_MINUTES: int = Field(10, description="Interval for weather checks in minutes")
    FORECAST_TIME: time = Field(time(8, 0), description="Time for daily forecast posting (HH:MM)")
    ALERT_START_TIME: time = Field(time(8, 0), description="Start time for wind alerts (HH:MM)")
    ALERT_END_TIME: time = Field(time(17, 0), description="End time for wind alerts (HH:MM)")
    
    # Redis Settings
    REDIS_URL: str = Field(
        default_factory=lambda: os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"), 
        description="Redis URL for Celery"
    )
    
    # Database Settings
    DATABASE_URI: str = Field(
        default="sqlite:///instance/wind_bot.db",
        description="Database connection URI"
    )
    DATABASE_ENGINE_OPTIONS: Dict[str, Any] = Field(
        default_factory=lambda: {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        },
        description="SQLAlchemy database engine options"
    )
    
    # Web Settings
    SESSION_SECRET: str = Field("dev_secret_key", description="Secret key for Flask sessions")
    
    # LangChain Settings
    LANGSMITH_TRACING: bool = Field(True, description="Enable LangSmith tracing")
    LANGSMITH_ENDPOINT: str = Field("https://api.smith.langchain.com", description="LangSmith API endpoint")
    LANGSMITH_API_KEY: str = Field(..., description="LangSmith API key")
    LANGSMITH_PROJECT: str = Field("tq_wind_bot", description="LangSmith project name")
    
    # OpenAI Settings
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_MODEL: str = Field("gpt-4o", description="OpenAI model to use")
    
    @field_validator('DATABASE_URI', mode='before')
    @classmethod
    def set_database_uri(cls, v):
        """Priority: DATABASE_URL environment variable, then default value"""
        return os.environ.get("DATABASE_URL", v)
    
    @field_validator('FORECAST_TIME', 'ALERT_START_TIME', 'ALERT_END_TIME')
    @classmethod
    def validate_time(cls, v):
        if not isinstance(v, time):
            try:
                hour, minute = map(int, v.split(':'))
                return time(hour, minute)
            except (ValueError, AttributeError):
                raise ValueError("Time must be in HH:MM format")
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
