"""
SQLModel definitions representing the database schema.
These are used by the repositories for database interactions.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

# Note: These models are technically part of the infrastructure persistence layer.
# If following strict DDD, the pure domain models would be separate.
# However, SQLModel often serves as both ORM model and data structure.


class BotStats(SQLModel, table=True):
    """Statistics about the bot's usage, stored in the database."""

    __tablename__ = "bot_stats"  # Optional: Explicit table name if needed

    id: Optional[int] = Field(default=None, primary_key=True)
    # --- Counters ---
    messages_processed: int = Field(default=0)
    weather_commands: int = Field(default=0)
    forecast_commands: int = Field(default=0)
    language_commands: int = Field(default=0)  # Assuming language command exists
    debug_commands: int = Field(default=0)  # Assuming debug command exists
    start_commands: int = Field(default=0)  # Assuming start command exists
    help_commands: int = Field(default=0)  # Assuming help command exists
    scheduled_checks: int = Field(default=0)  # From scheduled task
    alerts_sent: int = Field(default=0)
    # --- Gauges ---
    active_users: int = Field(default=0)  # Gauge updated periodically
    # --- Timestamps ---
    # Use default_factory for values generated on creation if not provided
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    date: Optional[datetime] = Field(default=None, index=True)  # Store the specific date for aggregation


class WeatherLog(SQLModel, table=True):
    """Log of weather data fetched, stored in the database."""

    __tablename__ = "weather_log"  # Optional: Explicit table name

    id: Optional[int] = Field(default=None, primary_key=True)
    temperature: Optional[float] = Field(default=None)
    wind_speed_knots: Optional[float] = Field(default=None)
    wind_speed_ms: Optional[float] = Field(default=None)
    has_rain: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
