"""
Test cases for Celery tasks.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from config import settings
from models import MessageType
from tasks import check_weather, send_daily_forecast, send_wind_alert, wind_alert_sent_today


class TestCeleryTasks:
    """Test Celery tasks"""
    
    def setup_method(self):
        """Reset global state before each test"""
        global wind_alert_sent_today
        wind_alert_sent_today = False
    
    def test_check_weather(self, mock_weather_service, sample_weather_data):
        """Test the check_weather task"""
        with patch('tasks.WeatherService', return_value=mock_weather_service):
            # Test normal execution
            result = check_weather()
            
            # Verify that get_current_weather was called
            mock_weather_service.get_current_weather.assert_called_once()
            
            # Check the result
            assert result is not None
            assert "timestamp" in result
            assert "weather_data" in result
            assert "temperature" in result["weather_data"]
            assert "wind_speed_knots" in result["weather_data"]
            assert "wind_speed_ms" in result["weather_data"]
            assert "has_rain" in result["weather_data"]
    
    def test_check_weather_error(self, mock_weather_service):
        """Test error handling in the check_weather task"""
        # Set up the mock to return None (error)
        mock_weather_service.get_current_weather.return_value = None
        
        with patch('tasks.WeatherService', return_value=mock_weather_service):
            # Test execution with error
            result = check_weather()
            
            # The task should return None on error
            assert result is None
    
    @patch('tasks.send_message')
    def test_send_daily_forecast(self, mock_send_message, mock_weather_service, sample_weather_data):
        """Test the send_daily_forecast task"""
        with patch('tasks.WeatherService', return_value=mock_weather_service):
            # Set up allowed chat IDs
            with patch('tasks.settings') as mock_settings:
                mock_settings.ALLOWED_CHAT_IDS = [123, 456]
                mock_settings.DEFAULT_LANGUAGE = "en"
                
                # Run the task
                send_daily_forecast()
                
                # Verify that get_current_weather was called
                mock_weather_service.get_current_weather.assert_called_once()
                
                # Verify that send_message was called for each chat ID
                assert mock_send_message.delay.call_count == 2
                
                # Check the arguments for the first call
                args1 = mock_send_message.delay.call_args_list[0][0][0]
                assert args1.message_type == MessageType.DAILY_FORECAST
                assert args1.chat_id == 123
                assert args1.language == "en"
    
    @patch('tasks.send_message')
    def test_send_wind_alert(self, mock_send_message, sample_weather_data):
        """Test the send_wind_alert task"""
        # Set up allowed chat IDs
        with patch('tasks.settings') as mock_settings:
            mock_settings.ALLOWED_CHAT_IDS = [123, 456]
            mock_settings.DEFAULT_LANGUAGE = "en"
            
            # Run the task
            send_wind_alert(sample_weather_data.model_dump())
            
            # Verify that send_message was called for each chat ID
            assert mock_send_message.delay.call_count == 2
            
            # Check the arguments for the first call
            args1 = mock_send_message.delay.call_args_list[0][0][0]
            assert args1.message_type == MessageType.WIND_ALERT
            assert args1.chat_id == 123
            assert args1.language == "en"
    
    @patch('tasks.should_send_wind_alert')
    @patch('tasks.send_wind_alert')
    def test_wind_alert_tracking(self, mock_send_wind_alert, mock_should_send, mock_weather_service, sample_weather_data):
        """Test that wind alerts are only sent once per day"""
        with patch('tasks.WeatherService', return_value=mock_weather_service):
            # Set up the mocks
            mock_should_send.return_value = True
            
            # Set first check of day and verify flag is reset
            with patch('tasks.datetime') as mock_datetime:
                mock_now = MagicMock()
                mock_now.hour = 8
                mock_now.minute = 0
                mock_now.date.return_value = datetime(2023, 1, 1).date()
                mock_datetime.now.return_value = mock_now
                
                with patch('tasks.settings') as mock_settings:
                    mock_settings.ALERT_START_TIME = datetime(2023, 1, 1, 8, 0, 0).time()
                    mock_settings.WEATHER_CHECK_INTERVAL_MINUTES = 10
                    
                    # First check
                    check_weather()
                    
                    # Verify that send_wind_alert was called
                    mock_send_wind_alert.delay.assert_called_once()
                    
                    # Reset mock
                    mock_send_wind_alert.delay.reset_mock()
                    
                    # Second check (should not send alert again)
                    check_weather()
                    
                    # Verify that send_wind_alert was NOT called again
                    mock_send_wind_alert.delay.assert_not_called()
