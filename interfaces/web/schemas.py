"""
Pydantic Schemas (Data Transfer Objects) for the Web API.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

# --- WeatherLog Schemas --- #


class WeatherLogBase(BaseModel):
    temperature: Optional[float] = None
    wind_speed_knots: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    has_rain: Optional[bool] = False


class WeatherLogCreate(WeatherLogBase):
    pass


class WeatherLogRead(WeatherLogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True  # Allows mapping from SQLAlchemy models


# --- BotStats Schemas --- #


class BotStatsBase(BaseModel):
    messages_processed: int = 0
    weather_commands: int = 0
    forecast_commands: int = 0
    wind_commands: int = 0
    alerts_sent: int = 0
    active_users: int = 0


class BotStatsUpdate(BaseModel):
    # Use Optional for updates, allowing partial updates
    messages_processed: Optional[int] = None
    weather_commands: Optional[int] = None
    forecast_commands: Optional[int] = None
    wind_commands: Optional[int] = None
    alerts_sent: Optional[int] = None
    active_users: Optional[int] = None


class BotStatsRead(BotStatsBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True  # Allows mapping from SQLAlchemy models
