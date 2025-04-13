"""
LangChain tools for the wind sports Telegram bot.
"""
import json
from typing import Optional, Dict, Any, List, Type

# Use langchain_core for BaseTool
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from domain.models.weather import WeatherData
from infrastructure.weather.openweather_service import OpenWeatherService
from application.use_cases.unit_conversion import ms_to_knots, knots_to_ms


class WindSpeedConversion(BaseModel):
    """Input/output schema for wind speed conversion tools"""
    speed: float = Field(..., description="Wind speed value to convert")


class WindSpeedToKnotsTool(BaseTool):
    """Tool for converting wind speed from m/s to knots"""
    name: str = "convert_wind_ms_to_knots"
    description: str = "Convert wind speed from meters per second (m/s) to knots"
    args_schema: Type[BaseModel] = WindSpeedConversion
    
    def _run(self, speed: float) -> Dict[str, Any]:
        """Convert wind speed from m/s to knots"""
        try:
            knots = ms_to_knots(speed)
            return {
                "original_speed": speed,
                "original_unit": "m/s",
                "converted_speed": knots,
                "converted_unit": "knots"
            }
        except Exception as e:
            return {"error": str(e)}


class WindSpeedToMSTool(BaseTool):
    """Tool for converting wind speed from knots to m/s"""
    name: str = "convert_wind_knots_to_ms"
    description: str = "Convert wind speed from knots to meters per second (m/s)"
    args_schema: Type[BaseModel] = WindSpeedConversion
    
    def _run(self, speed: float) -> Dict[str, Any]:
        """Convert wind speed from knots to m/s"""
        try:
            ms = knots_to_ms(speed)
            return {
                "original_speed": speed,
                "original_unit": "knots",
                "converted_speed": ms,
                "converted_unit": "m/s"
            }
        except Exception as e:
            return {"error": str(e)}


class GetCurrentWeatherInput(BaseModel):
    """Input schema for the get current weather tool"""
    location: Optional[str] = Field(
        None, 
        description="Optional location name. If not provided, the default location will be used."
    )


class GetCurrentWeatherTool(BaseTool):
    """Tool for retrieving current weather data"""
    name: str = "get_current_weather"
    description: str = "Get current weather data for kitesurfing and windsurfing at the configured location"
    args_schema: Type[BaseModel] = GetCurrentWeatherInput
    weather_service: OpenWeatherService = Field(default=None, exclude=True)
    
    def __init__(self, weather_service: OpenWeatherService):
        super().__init__(weather_service=weather_service)
    
    def _run(self, location: Optional[str] = None) -> Dict[str, Any]:
        """Get current weather data"""
        try:
            weather_data = self.weather_service.get_current_weather()
            
            if not weather_data:
                return {"error": "Failed to retrieve weather data"}
            
            # Format the response in a way that's useful for the LLM
            return {
                "temperature": {
                    "value": weather_data.temperature,
                    "unit": "Celsius",
                    "feels_like": weather_data.feels_like
                },
                "wind": {
                    "speed": {
                        "value_ms": weather_data.wind.speed_ms,
                        "value_knots": weather_data.wind.speed_knots
                    },
                    "gust": {
                        "value_ms": weather_data.wind.gust_ms,
                        "value_knots": weather_data.wind.gust_knots
                    } if weather_data.wind.gust_ms else None
                },
                "conditions": [
                    {
                        "main": c.main,
                        "description": c.description
                    } for c in weather_data.weather_conditions
                ],
                "has_rain": weather_data.has_rain,
                "has_snow": weather_data.has_snow,
                "humidity": weather_data.humidity,
                "clouds": weather_data.clouds,
                "timestamp": weather_data.timestamp.isoformat(),
                "location": {
                    "latitude": self.weather_service.latitude,
                    "longitude": self.weather_service.longitude,
                    "name": weather_data.location_name,
                    "country_code": weather_data.country_code
                }
            }
        except Exception as e:
            return {"error": str(e)}