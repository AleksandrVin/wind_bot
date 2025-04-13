"""
Test cases for the weather service.
"""

import pytest
from unittest.mock import MagicMock

from config import settings
from models import WindSpeed, WeatherData
from weather import WeatherService


class TestWeatherService:
    """Test the WeatherService class"""

    def test_init_with_defaults(self):
        """Test initialization with default values"""
        service = WeatherService()

        assert service.api_key == settings.OPENWEATHER_API_KEY
        assert service.latitude == settings.LATITUDE
        assert service.longitude == settings.LONGITUDE
        assert service.base_url == "https://api.openweathermap.org/data/2.5"

    def test_init_with_custom_values(self):
        """Test initialization with custom values"""
        service = WeatherService(api_key="test_key", latitude=10.0, longitude=20.0)

        assert service.api_key == "test_key"
        assert service.latitude == 10.0
        assert service.longitude == 20.0

    def test_get_current_weather(self, mock_requests, sample_weather_response):
        """Test getting current weather data"""
        service = WeatherService()
        result = service.get_current_weather()

        # Check that the request was made correctly
        mock_requests.assert_called_once()
        url = mock_requests.call_args[0][0]
        params = mock_requests.call_args[1]["params"]

        assert url == "https://api.openweathermap.org/data/2.5/weather"
        assert params["lat"] == settings.LATITUDE
        assert params["lon"] == settings.LONGITUDE
        assert params["appid"] == settings.OPENWEATHER_API_KEY
        assert params["units"] == "metric"

        # Check that the result is parsed correctly
        assert isinstance(result, WeatherData)
        assert result.temperature == sample_weather_response["main"]["temp"]
        assert result.feels_like == sample_weather_response["main"]["feels_like"]
        assert result.humidity == sample_weather_response["main"]["humidity"]
        assert result.wind.speed_ms == sample_weather_response["wind"]["speed"]
        assert result.wind.gust_ms == sample_weather_response["wind"]["gust"]
        assert result.clouds == sample_weather_response["clouds"]["all"]
        assert len(result.weather_conditions) == len(sample_weather_response["weather"])
        assert result.weather_conditions[0].id == sample_weather_response["weather"][0]["id"]
        assert result.weather_conditions[0].main == sample_weather_response["weather"][0]["main"]
        assert result.weather_conditions[0].description == sample_weather_response["weather"][0]["description"]

    def test_get_current_weather_error(self, mock_requests):
        """Test error handling when getting current weather data"""
        # Configure the mock to raise an exception
        mock_requests.side_effect = Exception("Test error")

        service = WeatherService()
        result = service.get_current_weather()

        # The method should return None on error
        assert result is None


class TestWindSpeed:
    """Test the WindSpeed model"""

    def test_speed_conversion(self):
        """Test wind speed conversion between m/s and knots"""
        wind = WindSpeed(speed_ms=5.0, gust_ms=7.5)

        # Test conversion from m/s to knots
        assert wind.speed_knots == pytest.approx(5.0 * 1.94384, abs=0.01)
        assert wind.gust_knots == pytest.approx(7.5 * 1.94384, abs=0.01)

    def test_gust_optional(self):
        """Test that gust speed is optional"""
        wind = WindSpeed(speed_ms=5.0)

        assert wind.speed_ms == 5.0
        assert wind.gust_ms is None
        assert wind.speed_knots == pytest.approx(5.0 * 1.94384, abs=0.01)
        assert wind.gust_knots is None


class TestWeatherData:
    """Test the WeatherData model"""

    def test_has_rain(self, sample_weather_data):
        """Test the has_rain property"""
        # Default sample data has no rain
        assert not sample_weather_data.has_rain

        # Add rain data
        sample_weather_data.rain_1h = 1.5
        assert sample_weather_data.has_rain

        # Reset and check with weather condition
        sample_weather_data.rain_1h = None
        sample_weather_data.weather_conditions[0].main = "Rain"
        assert sample_weather_data.has_rain

    def test_has_snow(self, sample_weather_data):
        """Test the has_snow property"""
        # Default sample data has no snow
        assert not sample_weather_data.has_snow

        # Add snow data
        sample_weather_data.snow_1h = 1.5
        assert sample_weather_data.has_snow

        # Reset and check with weather condition
        sample_weather_data.snow_1h = None
        sample_weather_data.weather_conditions[0].main = "Snow"
        assert sample_weather_data.has_snow
