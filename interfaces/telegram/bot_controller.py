"""
Telegram bot interface layer.
Handles incoming Telegram updates and delegates processing to application use cases.
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Application Layer
from application.use_cases.process_telegram_command import ProcessTelegramCommandUseCase
from application.use_cases.process_telegram_message import ProcessTelegramMessageUseCase

# Configuration & Domain/DTOs
from config import settings
from infrastructure.llm.langchain_service import LangChainService

# Repository Interfaces (for type hinting)
# Infrastructure Layer (for instantiating dependencies)
from infrastructure.notifications.telegram_sender import TelegramNotificationService
from infrastructure.persistence.database import AsyncSessionLocal

# Import Repository Implementations and Async Session
from infrastructure.persistence.sql_stats_repository import SqlStatsRepository
from infrastructure.persistence.sql_weather_log_repository import (
    SqlWeatherLogRepository,
)
from infrastructure.weather.openweather_service import OpenWeatherService
from interfaces.web.schemas import (  # Use schemas for DB interaction
    BotStatsUpdate,
    WeatherLogCreate,
)

logger = logging.getLogger(__name__)


class TelegramBotController:
    """Controller handling Telegram updates and delegating to use cases."""

    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()

        # --- Dependency Instantiation (Replace with DI container ideally) ---
        self.notifier = TelegramNotificationService(token=token)
        self.weather_service = OpenWeatherService()  # Uses settings implicitly
        self.llm_service = LangChainService()  # Uses settings implicitly
        # Store Repository *Classes* for manual instantiation with session
        self.StatsRepository = SqlStatsRepository
        self.WeatherLogRepository = SqlWeatherLogRepository

        # Instantiate Use Cases with dependencies
        self.command_processor = ProcessTelegramCommandUseCase(self.notifier, self.weather_service)
        self.message_processor = ProcessTelegramMessageUseCase(self.notifier, self.llm_service)
        # ------------------------------------------------------------------

        self.active_users = set()  # Simple in-memory tracking for now
        self._register_handlers()
        logger.info("Telegram Bot Controller initialized.")

    def _register_handlers(self) -> None:
        """Register handlers for commands, messages, and errors."""
        commands = ["start", "help", "weather", "forecast", "language", "debug"]
        for command in commands:
            self.application.add_handler(CommandHandler(command, self.handle_command))

        self.application.add_handler(
            MessageHandler(
                (filters.ChatType.PRIVATE | filters.Entity("mention")) & filters.TEXT & ~filters.COMMAND,
                self.handle_text_message,
            )
        )
        self.application.add_handler(MessageHandler(filters.ALL, self._track_active_user_handler), group=-1)
        self.application.add_error_handler(self.error_handler)

    async def handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generic command handler that extracts info and calls the use case."""
        command = update.message.text.split()[0][1:].lower()
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        args = context.args
        user_context = context.user_data

        self._track_active_user(user_id)

        # Log stats update directly using repository within an async session
        try:
            async with AsyncSessionLocal() as session:
                stats_repo = self.StatsRepository(session)
                stats_data = BotStatsUpdate(**{f"{command}_commands": 1, "active_users": len(self.active_users)})
                await stats_repo.update_or_create_stats(stats_data)
        except Exception as e:
            logger.error(f"Failed to update stats for command '{command}': {e}", exc_info=True)
        # Session automatically handled by 'async with'

        # Execute the command processing use case
        await self.command_processor.execute(command, chat_id, user_id, args, user_context)

        # If weather/forecast, also log weather data
        if command in ["weather", "forecast"]:
            await self._log_current_weather_data()

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles non-command text messages by calling the message use case."""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message_text = update.message.text
        user_context = context.user_data

        self._track_active_user(user_id)

        # Log stats update directly using repository within an async session
        try:
            async with AsyncSessionLocal() as session:
                stats_repo = self.StatsRepository(session)
                stats_data = BotStatsUpdate(messages_processed=1, active_users=len(self.active_users))
                await stats_repo.update_or_create_stats(stats_data)
        except Exception as e:
            logger.error(f"Failed to update stats for message: {e}", exc_info=True)
        # Session automatically handled by 'async with'

        # Acknowledge receipt
        await update.message.chat.send_action(action="typing")

        # Execute the message processing use case
        await self.message_processor.execute(message_text, chat_id, user_context)

    async def _log_current_weather_data(self) -> None:
        """Fetches current weather and logs it to the database asynchronously."""
        try:
            weather_data = self.weather_service.get_current_weather()
            if weather_data:
                log_dto = WeatherLogCreate(
                    temperature=weather_data.temperature,
                    wind_speed_knots=weather_data.wind.speed_knots,
                    wind_speed_ms=weather_data.wind.speed_ms,
                    has_rain=bool(weather_data.rain_1h or weather_data.rain_3h),
                )
                async with AsyncSessionLocal() as session:
                    weather_repo = self.WeatherLogRepository(session)
                    await weather_repo.add_log(log_dto)
            else:
                logger.warning("Could not get weather data to log.")
        except Exception as e:
            logger.error(f"Failed to log weather data: {e}", exc_info=True)
        # Session automatically handled by 'async with'

    # --- Utility & Lifecycle Methods --- #

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(msg="Exception while handling an update:", exc_info=context.error)

    def _get_user_language(self, context: ContextTypes.DEFAULT_TYPE) -> str:
        return context.user_data.get("language", settings.DEFAULT_LANGUAGE)

    def _track_active_user(self, user_id: int) -> None:
        self.active_users.add(user_id)

    async def _track_active_user_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user:
            self._track_active_user(update.effective_user.id)

    async def start(self) -> None:
        logger.info("Starting Telegram bot polling...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Telegram bot started.")

    async def stop(self) -> None:
        logger.info("Stopping Telegram bot polling...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info("Telegram bot stopped.")
