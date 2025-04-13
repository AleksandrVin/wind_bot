"""
Pytest configuration and fixtures for the wind sports Telegram bot tests.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any

import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, patch

from config import settings, Language
from models import WeatherData, WindSpeed, WeatherCondition


@pytest.fixture
def sample_weather_data() -> WeatherData:
    """Return a sample WeatherData object for testing"""
    return WeatherData(
        temperature=25.5,
        feels_like=26.2,
        pressure=1012,
        humidity=65,
        wind=WindSpeed(
            speed_ms=5.2,
            gust_ms=7.8
        ),
        clouds=25,
        rain_1h=None,
        rain_3h=None,
        snow_1h=None,
        snow_3h=None,
        weather_conditions=[
            WeatherCondition(
                id=800,
                main="Clear",
                description="clear sky",
                icon="01d"
            )
        ],
        timestamp=datetime.now(),
        sunrise=datetime.now().replace(hour=6, minute=0, second=0, microsecond=0),
        sunset=datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
    )


@pytest.fixture
def sample_weather_response() -> Dict[str, Any]:
    """Return a sample OpenWeather API response for testing"""
    return {
        "coord": {"lon": 99.996, "lat": 12.36},
        "weather": [
            {
                "id": 800,
                "main": "Clear",
                "description": "clear sky",
                "icon": "01d"
            }
        ],
        "base": "stations",
        "main": {
            "temp": 25.5,
            "feels_like": 26.2,
            "temp_min": 25.0,
            "temp_max": 26.0,
            "pressure": 1012,
            "humidity": 65
        },
        "visibility": 10000,
        "wind": {
            "speed": 5.2,
            "deg": 120,
            "gust": 7.8
        },
        "clouds": {
            "all": 25
        },
        "dt": int(datetime.now().timestamp()),
        "sys": {
            "type": 1,
            "id": 9235,
            "country": "TH",
            "sunrise": int(datetime.now().replace(hour=6, minute=0, second=0, microsecond=0).timestamp()),
            "sunset": int(datetime.now().replace(hour=18, minute=0, second=0, microsecond=0).timestamp())
        },
        "timezone": 25200,
        "id": 1607530,
        "name": "Hua Hin",
        "cod": 200
    }


@pytest.fixture
def mock_weather_service(mocker: MockerFixture, sample_weather_data: WeatherData):
    """Mock the WeatherService class"""
    mock_service = MagicMock()
    mock_service.get_current_weather.return_value = sample_weather_data
    
    # Apply the mock
    mocker.patch('weather.WeatherService', return_value=mock_service)
    return mock_service


@pytest.fixture
def mock_llm_service(mocker: MockerFixture):
    """Mock the LLMService class"""
    mock_service = MagicMock()
    
    # Configure the process_message method to return a sample response
    async def mock_process_message(message, language=Language.ENGLISH):
        if language == Language.RUSSIAN:
            return "Mocked ответ на русском"
        return "Mocked response in English"
    
    mock_service.process_message = mock_process_message
    
    # Apply the mock
    mocker.patch('llm.LLMService', return_value=mock_service)
    return mock_service


@pytest.fixture
def mock_telegram_update():
    """Create a mock Telegram Update object"""
    update = MagicMock()
    update.effective_chat.id = 123456789
    update.effective_user.first_name = "Test"
    update.effective_user.mention_html.return_value = "<a href='tg://user?id=123456789'>Test</a>"
    update.message.text = "How's the wind today?"
    
    return update


@pytest.fixture
def mock_telegram_context():
    """Create a mock Telegram Context object"""
    context = MagicMock()
    context.user_data = {"language": Language.ENGLISH}
    context.args = []
    
    return context


@pytest.fixture
def mock_requests(mocker: MockerFixture, sample_weather_response: Dict[str, Any]):
    """Mock the requests library to return a sample weather response"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_weather_response
    mock_response.raise_for_status.return_value = None
    
    # Mock the requests.get method
    mock_get = mocker.patch('requests.get', return_value=mock_response)
    
    return mock_get
