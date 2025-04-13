"""
Weather utility functions for the wind sports Telegram bot.
"""

from datetime import datetime

from config import settings
from domain.models.weather import WeatherData


def is_within_alert_time_window() -> bool:
    """Check if current time is within the alert time window"""
    now = datetime.now().time()
    return settings.ALERT_START_TIME <= now <= settings.ALERT_END_TIME


def should_send_wind_alert(weather_data: WeatherData) -> bool:
    """
    Determine if a wind alert should be sent based on current weather data
    and threshold settings
    """
    if not is_within_alert_time_window():
        return False

    wind_speed_knots = weather_data.wind.speed_knots
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
    """Get appropriate emoji for wind speed"""
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
