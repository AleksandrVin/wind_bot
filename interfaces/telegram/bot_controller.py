"""
Telegram bot interface for the wind sports Telegram bot.
"""

import logging
from typing import Dict

import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from application.utils.message_formatting import format_weather_message
from config import Language, settings
from domain.models.messaging import BotMessage, MessageType
from domain.models.weather import WeatherData
from infrastructure.llm.langchain_service import LangChainService
from infrastructure.weather.openweather_service import OpenWeatherService

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBotController:
    """Controller for the Telegram bot interface"""

    def __init__(self, token: str):
        """Initialize the bot with the given token"""
        self.token = token
        self.application = Application.builder().token(token).build()
        self.weather_service = OpenWeatherService()
        self.llm_service = LangChainService()
        self.web_api_url = settings.WEB_API_URL  # Use URL from settings
        self.active_users = set()  # Set to track active users

        # Register handlers
        self._register_handlers()
        logger.info(f"Telegram Bot Controller initialized. Web API URL: {self.web_api_url}")

    def _register_handlers(self) -> None:
        """Register command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("weather", self.weather_command))
        self.application.add_handler(CommandHandler("forecast", self.forecast_command))
        self.application.add_handler(CommandHandler("language", self.language_command))
        self.application.add_handler(CommandHandler("debug", self.debug_command))

        # Message handler for text messages that mention the bot
        # Only respond to private chats or when mentioned in group chats
        self.application.add_handler(
            MessageHandler(
                (filters.ChatType.PRIVATE | filters.Entity("mention")) & filters.TEXT & ~filters.COMMAND,
                self.handle_message,
            )
        )

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
        is_admin = user_id in settings.ADMIN_USER_IDS if hasattr(settings, "ADMIN_USER_IDS") else False

        # Basic commands for all users
        help_text = (
            "*Available Commands:*\n\n"
            "/weather - Get current weather conditions\n"
            "/forecast - Get today's forecast\n"
            "/language - Set your preferred language (en/ru)\n"
            "/help - Show this help message"
        )

        # Add admin commands if user is admin
        if is_admin:
            help_text += "\n\n*Admin Commands:*\n/debug - Force send weather data to all chats"

        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

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
                        language=Language.ENGLISH,
                    )

                    # Send the message
                    await self.send_message(bot_message)
                    success_count += 1

                except Exception as e:
                    logger.error(f"Failed to send debug message to chat {chat_id}: {e}")
                    fail_count += 1

            # Send summary to the admin
            await update.message.reply_text(
                f"Debug weather data sent to {success_count} chats. {fail_count} failed.", parse_mode=ParseMode.MARKDOWN
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
                "Please specify a language code (en/ru).\nExample: /language en", parse_mode=ParseMode.MARKDOWN
            )
            return

        language = args[0].lower()

        if language not in [Language.ENGLISH, Language.RUSSIAN]:
            await update.message.reply_text(
                "Sorry, I only support English (en) and Russian (ru) languages.\nExample: /language en",
                parse_mode=ParseMode.MARKDOWN,
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
            await update.message.reply_text("Language set to English! 🇬🇧", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("Язык установлен на русский! 🇷🇺", parse_mode=ParseMode.MARKDOWN)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages using LLMService"""
        try:
            # Get user's language preference
            language = self._get_user_language(context)
            user_message = update.message.text

            # Acknowledge receipt (optional)
            await update.message.chat.send_action(action="typing")

            # Process message with LLM
            response_text = await self.llm_service.process_message(user_message, language)

            await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

            # Log stats
            self._update_stats("messages_processed")  # Count all handled messages

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            error_msg = (
                "Sorry, I couldn't process your request right now."
                if language == Language.ENGLISH
                else "Извините, я не смог обработать ваш запрос сейчас."
            )
            await update.message.reply_text(error_msg)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log Errors caused by Updates."""
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        # Optionally send a message to the user or admin
        if isinstance(update, Update) and update.effective_message:
            error_msg = (
                "Sorry, an internal error occurred."
                if self._get_user_language(context) == Language.ENGLISH
                else "Извините, произошла внутренняя ошибка."
            )
            await update.effective_message.reply_text(error_msg)

        # You might want to track specific Telegram errors
        if isinstance(context.error, TelegramError):
            logger.warning(f"Telegram API Error: {context.error}")

    def _get_user_language(self, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Get the user's preferred language from context or default."""
        return context.user_data.get("language", settings.DEFAULT_LANGUAGE)

    async def send_message(self, bot_message: BotMessage) -> None:
        """Format and send a message using the bot."""
        try:
            message_text = format_weather_message(
                bot_message.weather_data, bot_message.message_type, bot_message.language
            )
            await self.application.bot.send_message(
                chat_id=bot_message.chat_id, text=message_text, parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"Sent message type {bot_message.message_type} to chat {bot_message.chat_id}")
        except TelegramError as e:
            logger.error(f"Telegram error sending message to {bot_message.chat_id}: {e}")
            # Handle specific errors like bot blocked, chat not found etc.
            if "bot was blocked by the user" in str(e):
                logger.warning(f"Bot blocked by user in chat {bot_message.chat_id}. Removing from active users?")
                # Consider removing chat_id from settings.ALLOWED_CHAT_IDS if applicable
            # Re-raise or handle as needed
        except Exception as e:
            logger.error(f"Failed to send message to {bot_message.chat_id}: {e}", exc_info=True)

    def _log_weather_data(self, weather_data: WeatherData) -> None:
        """Log weather data by sending it to the web API"""
        try:
            log_payload = {
                "temperature": weather_data.temperature,
                "wind_speed_knots": weather_data.wind.speed_knots,
                "wind_speed_ms": weather_data.wind.speed_ms,
                "has_rain": bool(weather_data.rain_1h or weather_data.rain_3h),
            }
            response = requests.post(f"{self.web_api_url}/add_weather_log", json=log_payload, timeout=5)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            logger.debug("Successfully logged weather data to web API.")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to log weather data to web interface: {e}")
        except Exception as e:
            logger.error(f"Unexpected error logging weather data: {e}", exc_info=True)

    def _update_stats(self, stat_name: str, count: int = 1) -> None:
        """Update bot stats by sending data to the web API"""
        try:
            stats_payload: Dict[str, int] = {stat_name: count}
            # Always include active users count
            stats_payload["active_users"] = len(self.active_users)

            response = requests.post(f"{self.web_api_url}/update_stats", json=stats_payload, timeout=5)
            response.raise_for_status()  # Raise an exception for bad status codes
            logger.debug(f"Successfully updated stats ({stat_name}) in web API.")
        except requests.exceptions.RequestException as e:
            # Log the payload that failed for debugging
            logger.warning(f"Failed to update stats in web interface: {e}. Payload: {stats_payload}")
        except Exception as e:
            logger.error(f"Unexpected error updating stats: {e}", exc_info=True)

    def _track_active_user(self, update: Update) -> None:
        """Track active users for statistics"""
        if update and update.effective_user:
            self.active_users.add(update.effective_user.id)

    async def _track_active_user_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Async handler for tracking active users"""
        self._track_active_user(update)

    async def start(self) -> None:
        """Start the bot polling."""
        logger.info("Starting Telegram bot polling...")
        # Add active user tracking middleware if needed
        # self.application.add_handler(TypeHandler(Update, self._track_active_user_handler), group=-1)
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Telegram bot started.")

    async def stop(self) -> None:
        """Stop the bot polling."""
        logger.info("Stopping Telegram bot polling...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info("Telegram bot stopped.")
