"""
Domain models for weather data in the wind sports Telegram bot.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class WindSpeed(BaseModel):
    """Wind speed data with conversion utilities"""

    speed_ms: float = Field(..., description="Wind speed in meters per second")
    gust_ms: Optional[float] = Field(None, description="Wind gust speed in meters per second")

    @property
    def speed_knots(self) -> float:
        """Convert wind speed from m/s to knots"""
        return self.speed_ms * 1.94384

    @property
    def gust_knots(self) -> Optional[float]:
        """Convert wind gust speed from m/s to knots"""
        if self.gust_ms is not None:
            return self.gust_ms * 1.94384
        return None


class WeatherCondition(BaseModel):
    """Weather condition data"""

    id: int = Field(..., description="Weather condition ID")
    main: str = Field(..., description="Group of weather parameters (Rain, Snow, Clouds etc.)")
    description: str = Field(..., description="Weather condition within the group")
    icon: str = Field(..., description="Weather icon ID")


class WeatherData(BaseModel):
    """Current weather data"""

    temperature: float = Field(..., description="Temperature in Celsius")
    feels_like: float = Field(..., description="Temperature feels like in Celsius")
    pressure: int = Field(..., description="Atmospheric pressure in hPa")
    humidity: int = Field(..., description="Humidity in %")
    wind: WindSpeed = Field(..., description="Wind speed data")
    clouds: int = Field(..., description="Cloudiness in %")
    rain_1h: Optional[float] = Field(None, description="Rain volume for the last 1 hour, mm")
    rain_3h: Optional[float] = Field(None, description="Rain volume for the last 3 hours, mm")
    snow_1h: Optional[float] = Field(None, description="Snow volume for the last 1 hour, mm")
    snow_3h: Optional[float] = Field(None, description="Snow volume for the last 3 hours, mm")
    weather_conditions: List[WeatherCondition] = Field(..., description="Weather conditions")
    timestamp: datetime = Field(..., description="Data calculation time, unix, UTC")
    sunrise: datetime = Field(..., description="Sunrise time, unix, UTC")
    sunset: datetime = Field(..., description="Sunset time, unix, UTC")
    location_name: Optional[str] = Field(None, description="Name of the location")
    country_code: Optional[str] = Field(None, description="Country code of the location")

    @property
    def has_rain(self) -> bool:
        """Check if it's raining"""
        return (
            (self.rain_1h is not None and self.rain_1h > 0)
            or (self.rain_3h is not None and self.rain_3h > 0)
            or any(condition.main.lower() == "rain" for condition in self.weather_conditions)
        )

    @property
    def has_snow(self) -> bool:
        """Check if it's snowing"""
        return (
            (self.snow_1h is not None and self.snow_1h > 0)
            or (self.snow_3h is not None and self.snow_3h > 0)
            or any(condition.main.lower() == "snow" for condition in self.weather_conditions)
        )
