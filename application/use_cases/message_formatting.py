"""
Message formatting for the wind sports Telegram bot.
"""

from config import Language
from domain.models.weather import WeatherData
from domain.models.messaging import MessageType
from application.use_cases.weather_utils import get_weather_emoji, get_wind_emoji


def format_weather_message(weather_data: WeatherData, message_type: MessageType, language: str = "en") -> str:
    """Format weather data into a human-readable message with rich formatting"""
    emoji = get_weather_emoji(weather_data)
    wind_emoji = get_wind_emoji(weather_data.wind.speed_knots)

    date_str = weather_data.timestamp.strftime("%d.%m.%Y")
    time_str = weather_data.timestamp.strftime("%H:%M")

    gust_text = ""
    if weather_data.wind.gust_knots:
        gust_text = f" (gusts: {weather_data.wind.gust_knots:.1f} kn / {weather_data.wind.gust_ms:.1f} m/s)"

    if language == Language.ENGLISH:
        if message_type == MessageType.CURRENT_WEATHER:
            location_info = ""
            if weather_data.location_name:
                location_info = f" for {weather_data.location_name}"
                if weather_data.country_code:
                    location_info += f", {weather_data.country_code}"

            return (
                f"*Current Weather*{location_info} {emoji} ({date_str}, {time_str})\n\n"
                f"🌡️ Temperature: *{weather_data.temperature:.1f}°C* (feels like {weather_data.feels_like:.1f}°C)\n"
                f"{wind_emoji} Wind: *{weather_data.wind.speed_knots:.1f} kn / {weather_data.wind.speed_ms:.1f} m/s*{gust_text}\n"
                f"💧 Humidity: {weather_data.humidity}%\n"
                f"☁️ Clouds: {weather_data.clouds}%\n"
                f"🌅 Sunrise: {weather_data.sunrise.strftime('%H:%M')}\n"
                f"🌇 Sunset: {weather_data.sunset.strftime('%H:%M')}\n\n"
                f"Conditions: {', '.join(c.description for c in weather_data.weather_conditions)}"
            )
        elif message_type == MessageType.DAILY_FORECAST:
            location_info = ""
            if weather_data.location_name:
                location_info = f" for {weather_data.location_name}"
                if weather_data.country_code:
                    location_info += f", {weather_data.country_code}"

            return (
                f"*Daily Forecast*{location_info} {emoji} ({date_str})\n\n"
                f"🌡️ Temperature: *{weather_data.temperature:.1f}°C* (feels like {weather_data.feels_like:.1f}°C)\n"
                f"{wind_emoji} Wind: *{weather_data.wind.speed_knots:.1f} kn / {weather_data.wind.speed_ms:.1f} m/s*{gust_text}\n"
                f"💧 Humidity: {weather_data.humidity}%\n"
                f"☁️ Clouds: {weather_data.clouds}%\n"
                f"🌅 Sunrise: {weather_data.sunrise.strftime('%H:%M')}\n"
                f"🌇 Sunset: {weather_data.sunset.strftime('%H:%M')}\n\n"
                f"Have a great day! 🏄‍♂️🪁"
            )
        elif message_type == MessageType.WIND_ALERT:
            location_info = ""
            if weather_data.location_name:
                location_info = f" for {weather_data.location_name}"
                if weather_data.country_code:
                    location_info += f", {weather_data.country_code}"

            return (
                f"*Wind Alert!*{location_info} {wind_emoji}\n\n"
                f"Current wind speed is *{weather_data.wind.speed_knots:.1f} kn / {weather_data.wind.speed_ms:.1f} m/s*{gust_text}\n"
                f"Time to hit the water! 🏄‍♂️🪁"
            )
    elif language == Language.RUSSIAN:
        if message_type == MessageType.CURRENT_WEATHER:
            location_info = ""
            if weather_data.location_name:
                location_info = f" для {weather_data.location_name}"
                if weather_data.country_code:
                    location_info += f", {weather_data.country_code}"

            return (
                f"*Текущая погода*{location_info} {emoji} ({date_str}, {time_str})\n\n"
                f"🌡️ Температура: *{weather_data.temperature:.1f}°C* (ощущается как {weather_data.feels_like:.1f}°C)\n"
                f"{wind_emoji} Ветер: *{weather_data.wind.speed_knots:.1f} уз / {weather_data.wind.speed_ms:.1f} м/с*{gust_text}\n"
                f"💧 Влажность: {weather_data.humidity}%\n"
                f"☁️ Облачность: {weather_data.clouds}%\n"
                f"🌅 Восход: {weather_data.sunrise.strftime('%H:%M')}\n"
                f"🌇 Закат: {weather_data.sunset.strftime('%H:%M')}\n\n"
                f"Условия: {', '.join(c.description for c in weather_data.weather_conditions)}"
            )
        elif message_type == MessageType.DAILY_FORECAST:
            location_info = ""
            if weather_data.location_name:
                location_info = f" для {weather_data.location_name}"
                if weather_data.country_code:
                    location_info += f", {weather_data.country_code}"

            return (
                f"*Прогноз на день*{location_info} {emoji} ({date_str})\n\n"
                f"🌡️ Температура: *{weather_data.temperature:.1f}°C* (ощущается как {weather_data.feels_like:.1f}°C)\n"
                f"{wind_emoji} Ветер: *{weather_data.wind.speed_knots:.1f} уз / {weather_data.wind.speed_ms:.1f} м/с*{gust_text}\n"
                f"💧 Влажность: {weather_data.humidity}%\n"
                f"☁️ Облачность: {weather_data.clouds}%\n"
                f"🌅 Восход: {weather_data.sunrise.strftime('%H:%M')}\n"
                f"🌇 Закат: {weather_data.sunset.strftime('%H:%M')}\n\n"
                f"Хорошего дня! 🏄‍♂️🪁"
            )
        elif message_type == MessageType.WIND_ALERT:
            location_info = ""
            if weather_data.location_name:
                location_info = f" для {weather_data.location_name}"
                if weather_data.country_code:
                    location_info += f", {weather_data.country_code}"

            return (
                f"*Ветровая тревога!*{location_info} {wind_emoji}\n\n"
                f"Текущая скорость ветра *{weather_data.wind.speed_knots:.1f} уз / {weather_data.wind.speed_ms:.1f} м/с*{gust_text}\n"
                f"Время кататься! 🏄‍♂️🪁"
            )

    # Default to English if language not supported
    return format_weather_message(weather_data, message_type, Language.ENGLISH)
