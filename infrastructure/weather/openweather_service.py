"""
OpenWeather API service for the wind sports Telegram bot.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

import requests
from pydantic import ValidationError

from config import settings
from domain.models.weather import WeatherData, WindSpeed, WeatherCondition

logger = logging.getLogger(__name__)


class OpenWeatherService:
    """Service for retrieving weather data from OpenWeather API"""

    def __init__(self, api_key: str = None, latitude: float = None, longitude: float = None):
        """Initialize the weather service"""
        self.api_key = api_key or settings.OPENWEATHER_API_KEY
        self.latitude = latitude or settings.LATITUDE
        self.longitude = longitude or settings.LONGITUDE
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_current_weather(self) -> Optional[WeatherData]:
        """Get current weather data for the configured location"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                "lat": self.latitude,
                "lon": self.longitude,
                "appid": self.api_key,
                "units": "metric",  # Use metric units (temperature in Celsius, wind speed in m/s)
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return self._parse_weather_data(data)

        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return None
        except ValidationError as e:
            logger.error(f"Error parsing weather data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def _parse_weather_data(self, data: Dict[str, Any]) -> WeatherData:
        """Parse the OpenWeather API response into a WeatherData model"""
        wind_data = data.get("wind", {})
        wind = WindSpeed(speed_ms=wind_data.get("speed", 0.0), gust_ms=wind_data.get("gust"))

        weather_conditions = [
            WeatherCondition(
                id=condition.get("id", 0),
                main=condition.get("main", ""),
                description=condition.get("description", ""),
                icon=condition.get("icon", ""),
            )
            for condition in data.get("weather", [])
        ]

        # Extract rain and snow data if available
        rain_data = data.get("rain", {})
        snow_data = data.get("snow", {})

        return WeatherData(
            temperature=data.get("main", {}).get("temp", 0.0),
            feels_like=data.get("main", {}).get("feels_like", 0.0),
            pressure=data.get("main", {}).get("pressure", 0),
            humidity=data.get("main", {}).get("humidity", 0),
            wind=wind,
            clouds=data.get("clouds", {}).get("all", 0),
            rain_1h=rain_data.get("1h"),
            rain_3h=rain_data.get("3h"),
            snow_1h=snow_data.get("1h"),
            snow_3h=snow_data.get("3h"),
            weather_conditions=weather_conditions,
            timestamp=datetime.fromtimestamp(data.get("dt", 0)),
            sunrise=datetime.fromtimestamp(data.get("sys", {}).get("sunrise", 0)),
            sunset=datetime.fromtimestamp(data.get("sys", {}).get("sunset", 0)),
            location_name=data.get("name"),
            country_code=data.get("sys", {}).get("country"),
        )
