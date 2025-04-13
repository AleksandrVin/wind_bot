"""
Test cases for the Telegram bot.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from config import Language
from bot import WindSportsBot
from models import BotMessage, MessageType


@pytest.mark.asyncio
class TestTelegramBot:
    """Test the Telegram bot functionality"""
    
    @pytest.fixture
    def bot(self):
        """Create a bot instance for testing"""
        with patch('bot.Application') as mock_application:
            # Mock the application builder
            mock_builder = MagicMock()
            mock_builder.token.return_value = mock_builder
            mock_builder.build.return_value = MagicMock()
            mock_application.builder.return_value = mock_builder
            
            # Create the bot with a test token
            bot = WindSportsBot("test_token")
            
            # Replace async methods with AsyncMock
            bot.start_command = AsyncMock()
            bot.help_command = AsyncMock()
            bot.weather_command = AsyncMock()
            bot.forecast_command = AsyncMock()
            bot.wind_command = AsyncMock()
            bot.language_command = AsyncMock()
            bot.handle_message = AsyncMock()
            bot.error_handler = AsyncMock()
            bot.send_message = AsyncMock()
            
            return bot
    
    async def test_start_command(self, bot, mock_telegram_update, mock_telegram_context):
        """Test the /start command handler"""
        # Call the handler directly
        await bot.start_command(mock_telegram_update, mock_telegram_context)
        
        # Verify that reply_html was called
        mock_telegram_update.message.reply_html.assert_called_once()
        
        # Check the content of the message
        call_args = mock_telegram_update.message.reply_html.call_args[0][0]
        assert "Hi" in call_args
        assert "Wind Sports Assistant Bot" in call_args
    
    async def test_help_command(self, bot, mock_telegram_update, mock_telegram_context):
        """Test the /help command handler"""
        # Call the handler directly
        await bot.help_command(mock_telegram_update, mock_telegram_context)
        
        # Verify that reply_text was called
        mock_telegram_update.message.reply_text.assert_called_once()
        
        # Check the content of the message
        call_args = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "Available Commands" in call_args
        assert "/weather" in call_args
        assert "/forecast" in call_args
        assert "/wind" in call_args
        assert "/language" in call_args
    
    async def test_weather_command(self, bot, mock_telegram_update, mock_telegram_context, mock_weather_service):
        """Test the /weather command handler"""
        # Set up the mock weather service to return data
        bot.weather_service = mock_weather_service
        
        # Call the handler directly
        await bot.weather_command(mock_telegram_update, mock_telegram_context)
        
        # Verify that get_current_weather was called
        mock_weather_service.get_current_weather.assert_called_once()
        
        # Verify that reply_text was called
        mock_telegram_update.message.reply_text.assert_called_once()
    
    async def test_weather_command_error(self, bot, mock_telegram_update, mock_telegram_context, mock_weather_service):
        """Test error handling in the /weather command handler"""
        # Set up the mock weather service to return None (error)
        mock_weather_service.get_current_weather.return_value = None
        bot.weather_service = mock_weather_service
        
        # Call the handler directly
        await bot.weather_command(mock_telegram_update, mock_telegram_context)
        
        # Verify that reply_text was called with an error message
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "Sorry" in call_args
        assert "couldn't retrieve" in call_args
    
    async def test_language_command(self, bot, mock_telegram_update, mock_telegram_context):
        """Test the /language command handler"""
        # Test with no language argument
        await bot.language_command(mock_telegram_update, mock_telegram_context)
        
        # Verify that reply_text was called with an error message
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "specify a language" in call_args
        
        # Reset mocks
        mock_telegram_update.message.reply_text.reset_mock()
        
        # Test with an invalid language
        mock_telegram_context.args = ["fr"]
        await bot.language_command(mock_telegram_update, mock_telegram_context)
        
        # Verify that reply_text was called with an error message
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "only support English" in call_args
        
        # Reset mocks
        mock_telegram_update.message.reply_text.reset_mock()
        
        # Test with English
        mock_telegram_context.args = ["en"]
        await bot.language_command(mock_telegram_update, mock_telegram_context)
        
        # Verify that reply_text was called with a success message
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "Language set to English" in call_args
        assert mock_telegram_context.user_data["language"] == Language.ENGLISH
        
        # Reset mocks
        mock_telegram_update.message.reply_text.reset_mock()
        
        # Test with Russian
        mock_telegram_context.args = ["ru"]
        await bot.language_command(mock_telegram_update, mock_telegram_context)
        
        # Verify that reply_text was called with a success message
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "Язык установлен на русский" in call_args
        assert mock_telegram_context.user_data["language"] == Language.RUSSIAN
    
    async def test_handle_message(self, bot, mock_telegram_update, mock_telegram_context, mock_llm_service):
        """Test the message handler"""
        # Set up the mock LLM service
        bot.llm_service = mock_llm_service
        
        # Call the handler directly
        await bot.handle_message(mock_telegram_update, mock_telegram_context)
        
        # Verify that send_action was called
        mock_telegram_update.message.chat.send_action.assert_called_once_with(action="typing")
        
        # Verify that process_message was called
        bot.llm_service.process_message.assert_awaited_once_with(
            mock_telegram_update.message.text,
            mock_telegram_context.user_data["language"]
        )
        
        # Verify that reply_text was called with the response
        mock_telegram_update.message.reply_text.assert_called_once()
    
    async def test_handle_message_error(self, bot, mock_telegram_update, mock_telegram_context, mock_llm_service):
        """Test error handling in the message handler"""
        # Set up the mock LLM service to raise an exception
        bot.llm_service.process_message.side_effect = Exception("Test error")
        
        # Call the handler directly
        await bot.handle_message(mock_telegram_update, mock_telegram_context)
        
        # Verify that reply_text was called with an error message
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args[0][0]
        assert "Sorry" in call_args
        assert "error" in call_args
    
    async def test_send_message(self, bot, sample_weather_data):
        """Test the send_message method"""
        # Create a bot message
        bot_message = BotMessage(
            message_type=MessageType.CURRENT_WEATHER,
            weather_data=sample_weather_data,
            chat_id=123456789,
            language=Language.ENGLISH
        )
        
        # Mock the Bot class
        with patch('bot.Bot') as mock_bot_class:
            mock_bot_instance = MagicMock()
            mock_bot_instance.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot_instance
            
            # Call the method
            await bot.send_message(bot_message)
            
            # Verify that Bot was instantiated with the token
            mock_bot_class.assert_called_once_with(token=bot.token)
            
            # Verify that send_message was called
            mock_bot_instance.send_message.assert_awaited_once()
            
            # Check the arguments
            call_kwargs = mock_bot_instance.send_message.call_args[1]
            assert call_kwargs["chat_id"] == bot_message.chat_id
            assert "Current Weather" in call_kwargs["text"]
            assert call_kwargs["parse_mode"] == "MARKDOWN"
