"""
Utility functions related to weather data processing and presentation.
"""

from datetime import datetime

from application.utils.unit_conversion import ms_to_knots
from config import settings
from domain.models.weather import WeatherData


def is_within_alert_time_window() -> bool:
    """Check if current time is within the alert time window"""
    now = datetime.now().time()
    return settings.ALERT_START_TIME <= now <= settings.ALERT_END_TIME


def should_send_wind_alert(weather_data: WeatherData) -> bool:
    """
    Determine if a wind alert should be sent based on current weather data
    and threshold settings.
    Assumes wind speed in WeatherData is in m/s.
    """
    if not is_within_alert_time_window():
        return False

    # Convert m/s from weather_data to knots for comparison
    wind_speed_knots = ms_to_knots(weather_data.wind.speed_ms)
    return wind_speed_knots >= settings.WIND_THRESHOLD_KNOTS


def get_weather_emoji(weather_data: WeatherData) -> str:
    """Get appropriate emoji for weather conditions"""
    if not weather_data.weather_conditions:
        return "🌤️"

    condition = weather_data.weather_conditions[0].main.lower()

    if weather_data.has_rain:
        return "🌧️"
    if weather_data.has_snow:
        return "❄️"

    mapping = {
        "clear": "☀️",
        "clouds": "☁️",
        "mist": "🌫️",
        "fog": "🌫️",
        "haze": "🌫️",
        "smoke": "🌫️",
        "dust": "🌫️",
        "sand": "🌫️",
        "ash": "🌫️",
        "squall": "💨",
        "tornado": "🌪️",
        "thunderstorm": "⛈️",
        "drizzle": "🌦️",
    }

    return mapping.get(condition, "🌤️")


def get_wind_emoji(speed_knots: float) -> str:
    """Get appropriate emoji for wind speed in knots."""
    if speed_knots < 5:
        return "🪶"  # light breeze
    elif speed_knots < 10:
        return "🍃"  # moderate breeze
    elif speed_knots < 15:
        return "💨"  # fresh breeze
    elif speed_knots < 20:
        return "🌬️"  # strong breeze
    elif speed_knots < 30:
        return "🚩"  # near gale
    else:
        return "🌪️"  # gale or stronger
