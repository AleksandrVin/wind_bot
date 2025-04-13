"""
Telegram bot interface for the wind sports Telegram bot.
"""
import asyncio
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any

from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

from config import settings, Language
from domain.models.messaging import BotMessage, MessageType
from domain.models.weather import WeatherData
from infrastructure.llm.langchain_service import LangChainService
from infrastructure.weather.openweather_service import OpenWeatherService
from application.use_cases.message_formatting import format_weather_message

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBotController:
    """Controller for the Telegram bot interface"""
    
    def __init__(self, token: str):
        """Initialize the bot with the given token"""
        self.token = token
        self.application = Application.builder().token(token).build()
        self.weather_service = OpenWeatherService()
        self.llm_service = LangChainService()
        self.web_api_url = "http://localhost:5000/api"  # URL to the web API
        self.active_users = set()  # Set to track active users
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("weather", self.weather_command))
        self.application.add_handler(CommandHandler("forecast", self.forecast_command))
        self.application.add_handler(CommandHandler("wind", self.wind_command))
        self.application.add_handler(CommandHandler("language", self.language_command))
        self.application.add_handler(CommandHandler("debug", self.debug_command))
        
        # Message handler for text messages that mention the bot
        # Only respond to private chats or when mentioned in group chats
        self.application.add_handler(MessageHandler(
            (filters.ChatType.PRIVATE | filters.Entity("mention")) & filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command"""
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        await update.message.reply_html(
            f"Hi {user.mention_html()}! 👋\n\n"
            f"I'm your Wind Sports Assistant Bot. I provide:\n\n"
            f"• Current weather conditions 🌤️\n"
            f"• Wind speed information 💨\n"
            f"• Daily forecasts ⛵\n"
            f"• Wind alerts when conditions are good 🏄‍♂️\n\n"
            f"Use /help to see available commands."
        )
        
        # Log the chat ID
        logger.info(f"Bot started in chat ID: {chat_id}")
        
        # If this chat isn't in allowed chats, inform the user
        if chat_id not in settings.ALLOWED_CHAT_IDS:
            await update.message.reply_text(
                "Note: This chat is not in the list of allowed chats for automated alerts. "
                "You can still use commands to get weather information."
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command"""
        user_id = update.effective_user.id
        is_admin = user_id in settings.ADMIN_USER_IDS if hasattr(settings, 'ADMIN_USER_IDS') else False
        
        # Basic commands for all users
        help_text = (
            "*Available Commands:*\n\n"
            "/weather - Get current weather conditions\n"
            "/forecast - Get today's forecast\n"
            "/wind - Get current wind speed\n"
            "/language - Set your preferred language (en/ru)\n"
            "/help - Show this help message"
        )
        
        # Add admin commands if user is admin
        if is_admin:
            help_text += (
                "\n\n*Admin Commands:*\n"
                "/debug - Force send weather data to all chats"
            )
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /weather command"""
        try:
            weather_data = self.weather_service.get_current_weather()
            
            if not weather_data:
                await update.message.reply_text("Sorry, I couldn't retrieve the weather data. Please try again later.")
                return
            
            # Get user's language preference
            language = self._get_user_language(context)
            
            # Format the message
            message = format_weather_message(weather_data, MessageType.CURRENT_WEATHER, language)
            
            # Send the message
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
            # Log stats and weather data to the web interface
            self._update_stats("weather_commands")
            self._log_weather_data(weather_data)
        
        except Exception as e:
            logger.error(f"Error in weather_command: {e}")
            await update.message.reply_text("Sorry, there was an error processing your request.")
    
    async def forecast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /forecast command"""
        try:
            weather_data = self.weather_service.get_current_weather()
            
            if not weather_data:
                await update.message.reply_text("Sorry, I couldn't retrieve the forecast data. Please try again later.")
                return
            
            # Get user's language preference
            language = self._get_user_language(context)
            
            # Format the message
            message = format_weather_message(weather_data, MessageType.DAILY_FORECAST, language)
            
            # Send the message
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
            # Log stats and weather data to the web interface
            self._update_stats("forecast_commands")
            self._log_weather_data(weather_data)
        
        except Exception as e:
            logger.error(f"Error in forecast_command: {e}")
            await update.message.reply_text("Sorry, there was an error processing your request.")
    
    async def wind_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /wind command"""
        try:
            weather_data = self.weather_service.get_current_weather()
            
            if not weather_data:
                await update.message.reply_text("Sorry, I couldn't retrieve the wind data. Please try again later.")
                return
            
            # Get user's language preference
            language = self._get_user_language(context)
            
            # Get the wind information
            wind_speed_knots = weather_data.wind.speed_knots
            wind_speed_ms = weather_data.wind.speed_ms
            
            gust_text = ""
            if weather_data.wind.gust_knots:
                gust_text = f"\nGusts: *{weather_data.wind.gust_knots:.1f} kn / {weather_data.wind.gust_ms:.1f} m/s*"
            
            location_info = ""
            if weather_data.location_name:
                if language == Language.ENGLISH:
                    location_info = f"\nLocation: {weather_data.location_name}"
                    if weather_data.country_code:
                        location_info += f", {weather_data.country_code}"
                else:
                    location_info = f"\nЛокация: {weather_data.location_name}"
                    if weather_data.country_code:
                        location_info += f", {weather_data.country_code}"
            
            if language == Language.ENGLISH:
                message = (
                    f"*Current Wind Speed*\n\n"
                    f"*{wind_speed_knots:.1f} knots / {wind_speed_ms:.1f} m/s*{gust_text}{location_info}"
                )
            else:
                message = (
                    f"*Текущая скорость ветра*\n\n"
                    f"*{wind_speed_knots:.1f} узлов / {wind_speed_ms:.1f} м/с*{gust_text}{location_info}"
                )
            
            # Send the message
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
            # Log stats
            self._update_stats("wind_commands")
            self._log_weather_data(weather_data)
        
        except Exception as e:
            logger.error(f"Error in wind_command: {e}")
            await update.message.reply_text("Sorry, there was an error processing your request.")
    
    async def debug_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /debug command (admin only)"""
        try:
            # Check if the user is an admin
            user_id = update.effective_user.id
            if user_id not in settings.ADMIN_USER_IDS:
                await update.message.reply_text("Sorry, this command is only available to admins.")
                return
            
            # Get current weather data
            weather_data = self.weather_service.get_current_weather()
            
            if not weather_data:
                await update.message.reply_text("Sorry, I couldn't retrieve the weather data. Please try again later.")
                return
            
            # Send weather data to all allowed chats
            success_count = 0
            fail_count = 0
            
            for chat_id in settings.ALLOWED_CHAT_IDS:
                try:
                    # Create a bot message
                    bot_message = BotMessage(
                        message_type=MessageType.CURRENT_WEATHER,
                        weather_data=weather_data,
                        chat_id=chat_id,
                        language=Language.ENGLISH
                    )
                    
                    # Send the message
                    await self.send_message(bot_message)
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send debug message to chat {chat_id}: {e}")
                    fail_count += 1
            
            # Send summary to the admin
            await update.message.reply_text(
                f"Debug weather data sent to {success_count} chats. {fail_count} failed.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Update stats
            self._update_stats("weather_commands", success_count)
            self._log_weather_data(weather_data)
            
        except Exception as e:
            logger.error(f"Error in debug_command: {e}")
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /language command"""
        args = context.args
        
        if not args:
            await update.message.reply_text(
                "Please specify a language code (en/ru).\n"
                "Example: /language en",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        language = args[0].lower()
        
        if language not in [Language.ENGLISH, Language.RUSSIAN]:
            await update.message.reply_text(
                "Sorry, I only support English (en) and Russian (ru) languages.\n"
                "Example: /language en",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Save the language preference in user data
        try:
            context.user_data.setdefault("language", language)
            # Update the value
            context.user_data["language"] = language
        except Exception as e:
            logger.error(f"Failed to set language in user_data: {e}")
        
        # Respond based on the selected language
        if language == Language.ENGLISH:
            await update.message.reply_text(
                "Language set to English! 🇬🇧",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "Язык установлен на русский! 🇷🇺",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages with hardcoded responses instead of LLM"""
        try:
            # Get user's language preference
            language = self._get_user_language(context)
            
            await update.message.chat.send_action(action="typing")
            
            # Provide a hardcoded response about available commands
            if language == Language.RUSSIAN:
                response = (
                    "Я могу предоставить информацию о погоде и ветре. "
                    "Пожалуйста, используйте следующие команды:\n\n"
                    "/weather - Текущие погодные условия\n"
                    "/forecast - Прогноз на сегодня\n"
                    "/wind - Текущая скорость ветра\n"
                    "/language - Выбрать язык (en/ru)\n"
                    "/help - Показать это сообщение помощи"
                )
            else:
                response = (
                    "I can provide weather and wind information. "
                    "Please use the following commands:\n\n"
                    "/weather - Current weather conditions\n"
                    "/forecast - Today's forecast\n"
                    "/wind - Current wind speed\n"
                    "/language - Set language (en/ru)\n"
                    "/help - Show this help message"
                )
            
            # Send the response
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
            # Log the message processing
            self._update_stats("messages_processed")
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
            language = self._get_user_language(context)
            # Send a generic error message based on the language preference
            if language == Language.RUSSIAN:
                await update.message.reply_text(
                    "Извините, произошла ошибка при обработке вашего сообщения."
                )
            else:
                await update.message.reply_text(
                    "Sorry, there was an error processing your message."
                )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the Telegram update pipeline"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Log the error details
        if update:
            logger.error(f"Update: {update}")
    
    def _get_user_language(self, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Get the user's preferred language"""
        # Default language
        language = settings.DEFAULT_LANGUAGE
        
        # Check if the user has a language preference
        if context and context.user_data and "language" in context.user_data:
            language = context.user_data["language"]
        
        return language
    
    async def send_message(self, bot_message: BotMessage) -> None:
        """Send a message using the bot"""
        try:
            # Get chat ID
            chat_id = bot_message.chat_id
            
            # Get the bot instance
            bot = self.application.bot
            
            # Format the message based on type and language
            if bot_message.message_type == MessageType.ERROR:
                # Send error message
                if bot_message.error_message:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=bot_message.error_message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    # Default error message
                    if bot_message.language == Language.RUSSIAN:
                        await bot.send_message(
                            chat_id=chat_id,
                            text="Произошла ошибка. Пожалуйста, попробуйте позже.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await bot.send_message(
                            chat_id=chat_id,
                            text="An error occurred. Please try again later.",
                            parse_mode=ParseMode.MARKDOWN
                        )
            else:
                # Weather-related message
                if bot_message.weather_data:
                    # Format the weather message
                    message = format_weather_message(
                        bot_message.weather_data,
                        bot_message.message_type,
                        bot_message.language
                    )
                    
                    # Send the message
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
        
        except TelegramError as e:
            logger.error(f"Telegram error sending message to {bot_message.chat_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    def _log_weather_data(self, weather_data: WeatherData) -> None:
        """Log weather data to the web interface"""
        try:
            # Convert datetime objects to strings for JSON serialization
            data = {
                "timestamp": weather_data.timestamp.isoformat(),
                "temperature": weather_data.temperature,
                "wind_speed_ms": weather_data.wind.speed_ms,
                "wind_speed_knots": weather_data.wind.speed_knots,
                "wind_gust_ms": weather_data.wind.gust_ms,
                "wind_gust_knots": weather_data.wind.gust_knots,
                "humidity": weather_data.humidity,
                "clouds": weather_data.clouds,
                "conditions": [c.main for c in weather_data.weather_conditions]
            }
            
            response = requests.post(
                f"{self.web_api_url}/add_weather_log",
                json=data,
                timeout=3  # Short timeout to avoid blocking the bot
            )
            
            if response.status_code != 201:
                logger.warning(f"Failed to log weather data in web interface: {response.text}")
            
        except Exception as e:
            logger.error(f"Error logging weather data in web interface: {e}")
    
    def _update_stats(self, stat_name: str, count: int = 1) -> None:
        """Update bot statistics in the web interface"""
        try:
            # Create data dictionary
            data = {
                "stat_name": stat_name,
                "count": count,
                "timestamp": datetime.now().isoformat()
            }
            
            # Also update active users
            if "active_users" not in data:
                data["active_users"] = len(self.active_users)
            
            response = requests.post(
                f"{self.web_api_url}/update_stats",
                json=data,
                timeout=3  # Short timeout to avoid blocking the bot
            )
            
            if response.status_code != 201:
                logger.warning(f"Failed to update stats in web interface: {response.text}")
            
        except Exception as e:
            logger.error(f"Error updating stats in web interface: {e}")
    
    def _track_active_user(self, update: Update) -> None:
        """Track active users for statistics"""
        if update and update.effective_user:
            self.active_users.add(update.effective_user.id)
            
    async def _track_active_user_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Async handler for tracking active users"""
        self._track_active_user(update)
    
    async def start(self) -> None:
        """Start the bot"""
        # Set up hooks to update our web interface
        self.application.add_handler(
            MessageHandler(
                filters.ALL,
                self._track_active_user_handler
            ),
            group=-1  # Run before other handlers
        )
        
        logger.info("Bot started")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
    async def stop(self) -> None:
        """Stop the bot"""
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()