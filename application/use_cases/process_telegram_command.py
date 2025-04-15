"""
Use Case: Process a command received via Telegram.
"""

import logging
from typing import Any, Dict, Optional

# Interfaces and Services
from application.interfaces.notification_service import AbstractNotificationService

# Other Use Cases (can be injected or instantiated)
from application.use_cases.generate_weather_report import GenerateWeatherReportUseCase
from config import Language, settings

# Domain Models & Utils
from domain.models.messaging import MessageType
from infrastructure.weather.openweather_service import OpenWeatherService  # Replace with AbstractWeatherService

logger = logging.getLogger(__name__)

# Type Alias for user context/preferences
UserContext = Dict[str, Any]


class ProcessTelegramCommandUseCase:
    def __init__(self, notifier: AbstractNotificationService, weather_service: OpenWeatherService):
        self.notifier = notifier
        self.weather_service = weather_service
        # Instantiate other use cases needed, or inject them
        self.report_generator = GenerateWeatherReportUseCase(weather_service)

    async def execute(
        self, command: str, chat_id: int, user_id: int, args: list[str], user_context: UserContext
    ) -> None:
        """Processes the command and sends a response.

        Args:
            command: The command name (e.g., 'start', 'weather').
            chat_id: The ID of the chat where the command was sent.
            user_id: The ID of the user who sent the command.
            args: List of arguments passed with the command.
            user_context: Dictionary holding user-specific data like language.
        """
        logger.info(f"Processing command '{command}' for chat {chat_id} from user {user_id} with args {args}")

        language = user_context.get("language", settings.DEFAULT_LANGUAGE)
        response_message: Optional[str] = None
        parse_mode: Optional[str] = "Markdown"
        new_language: Optional[str] = None

        try:
            if command == "start":
                parse_mode = "HTML"
                response_message = "Hi! 👋 I'm your Wind Sports Assistant Bot.\n\nUse /help to see available commands."
                # Check if chat is allowed (optional)
                if chat_id not in settings.ALLOWED_CHAT_IDS:
                    response_message += "\n\nNote: This chat is not in the list for automated alerts."

            elif command == "help":
                is_admin = user_id in settings.ADMIN_USER_IDS
                response_message = (
                    "*Available Commands:*\n\n"
                    "/weather - Current weather\n"
                    "/forecast - Today's forecast\n"
                    # "/wind - Current wind speed\n" # Covered by /weather
                    "/language [en/ru] - Set language\n"
                    "/help - Show this help message"
                )
                if is_admin:
                    response_message += "\n\n*Admin Commands:*\n/debug - (Not implemented via use case yet)"

            elif command == "weather":
                response_message = self.report_generator.execute(MessageType.CURRENT_WEATHER, language)
                if not response_message:
                    response_message = (
                        "Sorry, couldn't retrieve weather data."
                        if language == Language.ENGLISH
                        else "Извините, не удалось получить данные о погоде."
                    )

            elif command == "forecast":
                response_message = self.report_generator.execute(MessageType.DAILY_FORECAST, language)
                if not response_message:
                    response_message = (
                        "Sorry, couldn't retrieve forecast data."
                        if language == Language.ENGLISH
                        else "Извините, не удалось получить данные прогноза."
                    )

            elif command == "language":
                if not args:
                    response_message = "Please specify a language code (en/ru).\nExample: `/language en`"
                else:
                    lang_code = args[0].lower()
                    if lang_code in [Language.ENGLISH, Language.RUSSIAN]:
                        user_context["language"] = lang_code  # Update context
                        new_language = lang_code  # Signal change
                        response_message = (
                            "Language set to English! 🇬🇧"
                            if lang_code == Language.ENGLISH
                            else "Язык установлен на русский! 🇷🇺"
                        )
                    else:
                        response_message = "Sorry, only English (en) and Russian (ru) are supported."

            # Handle other commands or unknown commands
            else:
                logger.warning(f"Received unknown command: {command}")
                # Optionally send an "unknown command" message
                # response_message = "Sorry, I don't understand that command. Use /help."

            # Send response if one was generated
            if response_message:
                await self.notifier.send_notification(chat_id, response_message, parse_mode)

            # TODO: Persist language change if needed (e.g., via a UserPreferencesRepository)
            if new_language:
                logger.info(f"User {user_id} in chat {chat_id} changed language to {new_language}")
                # Call repository to save preference here

        except Exception as e:
            logger.error(f"Error processing command '{command}': {e}", exc_info=True)
            error_msg = (
                "Sorry, an error occurred processing your command."
                if language == Language.ENGLISH
                else "Извините, произошла ошибка при обработке команды."
            )
            # Avoid double notifying if initial send failed
            if response_message is None:
                await self.notifier.send_notification(chat_id, error_msg, parse_mode=None)
