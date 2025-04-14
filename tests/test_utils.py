"""
Test cases for utility functions.
"""

from datetime import datetime, time
from unittest.mock import patch

import pytest

from application.use_cases.weather_utils import (
    get_weather_emoji,
    get_wind_emoji,
    is_within_alert_time_window,
    should_send_wind_alert,
)
from application.use_cases.message_formatting import format_weather_message
from application.use_cases.unit_conversion import knots_to_ms, ms_to_knots
from config import Language
from domain.models.messaging import MessageType


class TestConversionFunctions:
    """Test wind speed conversion functions"""

    def test_ms_to_knots(self):
        """Test conversion from m/s to knots"""
        assert ms_to_knots(1.0) == pytest.approx(1.94384, abs=0.001)
        assert ms_to_knots(5.0) == pytest.approx(9.7192, abs=0.001)
        assert ms_to_knots(10.0) == pytest.approx(19.4384, abs=0.001)

    def test_knots_to_ms(self):
        """Test conversion from knots to m/s"""
        assert knots_to_ms(1.0) == pytest.approx(0.51444, abs=0.001)
        assert knots_to_ms(5.0) == pytest.approx(2.5722, abs=0.001)
        assert knots_to_ms(10.0) == pytest.approx(5.1444, abs=0.001)

    def test_conversion_roundtrip(self):
        """Test that conversions are reversible"""
        original = 5.0
        assert knots_to_ms(ms_to_knots(original)) == pytest.approx(original, abs=0.001)
        assert ms_to_knots(knots_to_ms(original)) == pytest.approx(original, abs=0.001)


class TestTimeWindowFunctions:
    """Test time window related functions"""

    @patch("application.utils.datetime")
    def test_is_within_alert_time_window(self, mock_datetime):
        """Test checking if current time is within alert window"""
        # Set up the mock datetime
        mock_datetime.now.return_value = datetime(2023, 1, 1, 10, 0, 0)  # 10:00 AM

        # Set alert window from 8 AM to 5 PM
        with patch("application.utils.settings") as mock_settings:
            mock_settings.ALERT_START_TIME = time(8, 0)
            mock_settings.ALERT_END_TIME = time(17, 0)

            assert is_within_alert_time_window() == True

        # Set time outside the window
        mock_datetime.now.return_value = datetime(2023, 1, 1, 7, 0, 0)  # 7:00 AM
        with patch("application.utils.settings") as mock_settings:
            mock_settings.ALERT_START_TIME = time(8, 0)
            mock_settings.ALERT_END_TIME = time(17, 0)

            assert is_within_alert_time_window() == False

        # Set time at the boundary
        mock_datetime.now.return_value = datetime(2023, 1, 1, 8, 0, 0)  # 8:00 AM
        with patch("application.utils.settings") as mock_settings:
            mock_settings.ALERT_START_TIME = time(8, 0)
            mock_settings.ALERT_END_TIME = time(17, 0)

            assert is_within_alert_time_window() == True

    @patch("application.utils.is_within_alert_time_window")
    def test_should_send_wind_alert(self, mock_is_within_window, sample_weather_data):
        """Test determining if a wind alert should be sent"""
        # Set up the mock time window check
        mock_is_within_window.return_value = True

        # Set wind threshold to 15 knots
        with patch("application.utils.settings") as mock_settings:
            mock_settings.WIND_THRESHOLD_KNOTS = 15.0

            # Test with wind below threshold
            sample_weather_data.wind.speed_ms = 5.0  # ~9.7 knots
            assert should_send_wind_alert(sample_weather_data) == False

            # Test with wind at threshold
            sample_weather_data.wind.speed_ms = 7.72  # ~15 knots
            assert should_send_wind_alert(sample_weather_data) == True

            # Test with wind above threshold
            sample_weather_data.wind.speed_ms = 10.0  # ~19.4 knots
            assert should_send_wind_alert(sample_weather_data) == True

        # Test outside time window
        mock_is_within_window.return_value = False
        sample_weather_data.wind.speed_ms = 10.0  # ~19.4 knots
        assert should_send_wind_alert(sample_weather_data) == False


class TestEmojiAndFormatting:
    """Test emoji selection and message formatting functions"""

    def test_get_weather_emoji(self, sample_weather_data):
        """Test emoji selection based on weather conditions"""
        # Test with clear weather
        sample_weather_data.weather_conditions[0].main = "Clear"
        assert get_weather_emoji(sample_weather_data) == "☀️"

        # Test with rain
        sample_weather_data.rain_1h = 1.5
        assert get_weather_emoji(sample_weather_data) == "🌧️"

        # Test with snow
        sample_weather_data.rain_1h = None
        sample_weather_data.snow_1h = 1.5
        assert get_weather_emoji(sample_weather_data) == "❄️"

        # Test with clouds
        sample_weather_data.snow_1h = None
        sample_weather_data.weather_conditions[0].main = "Clouds"
        assert get_weather_emoji(sample_weather_data) == "☁️"

        # Test with fog
        sample_weather_data.weather_conditions[0].main = "Fog"
        assert get_weather_emoji(sample_weather_data) == "🌫️"

        # Test with thunderstorm
        sample_weather_data.weather_conditions[0].main = "Thunderstorm"
        assert get_weather_emoji(sample_weather_data) == "⛈️"

    def test_get_wind_emoji(self):
        """Test emoji selection based on wind speed"""
        assert get_wind_emoji(3.0) == "🪶"  # light breeze
        assert get_wind_emoji(7.0) == "🍃"  # moderate breeze
        assert get_wind_emoji(12.0) == "💨"  # fresh breeze
        assert get_wind_emoji(18.0) == "🌬️"  # strong breeze
        assert get_wind_emoji(25.0) == "🚩"  # near gale
        assert get_wind_emoji(35.0) == "🌪️"  # gale or stronger

    def test_format_weather_message_english(self, sample_weather_data):
        """Test message formatting in English"""
        # Test current weather message
        message = format_weather_message(sample_weather_data, MessageType.CURRENT_WEATHER, Language.ENGLISH)
        assert "Current Weather" in message
        assert "Temperature" in message
        assert "Wind" in message
        assert "knots" in message
        assert "m/s" in message

        # Test forecast message
        message = format_weather_message(sample_weather_data, MessageType.DAILY_FORECAST, Language.ENGLISH)
        assert "Daily Forecast" in message
        assert "Have a great day" in message

        # Test wind alert message
        message = format_weather_message(sample_weather_data, MessageType.WIND_ALERT, Language.ENGLISH)
        assert "Wind Alert" in message
        assert "Time to hit the water" in message

    def test_format_weather_message_russian(self, sample_weather_data):
        """Test message formatting in Russian"""
        # Test current weather message
        message = format_weather_message(sample_weather_data, MessageType.CURRENT_WEATHER, Language.RUSSIAN)
        assert "Текущая погода" in message
        assert "Температура" in message
        assert "Ветер" in message
        assert "уз" in message  # узлов (knots in Russian)
        assert "м/с" in message

        # Test forecast message
        message = format_weather_message(sample_weather_data, MessageType.DAILY_FORECAST, Language.RUSSIAN)
        assert "Прогноз на день" in message
        assert "Хорошего дня" in message

        # Test wind alert message
        message = format_weather_message(sample_weather_data, MessageType.WIND_ALERT, Language.RUSSIAN)
        assert "Ветровая тревога" in message
        assert "Время кататься" in message
