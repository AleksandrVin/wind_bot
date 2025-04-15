"""
Use Case: Process a natural language message received via Telegram.
"""

import logging
from typing import Any, Dict

# Interfaces and Services
from application.interfaces.notification_service import AbstractNotificationService

# Domain Models & Config
from config import Language, settings
from infrastructure.llm.langchain_service import LangChainService  # Replace with AbstractLLMService if created

logger = logging.getLogger(__name__)

# Type Alias for user context/preferences
UserContext = Dict[str, Any]


class ProcessTelegramMessageUseCase:
    def __init__(
        self, notifier: AbstractNotificationService, llm_service: LangChainService
    ):  # Inject AbstractLLMService ideally
        self.notifier = notifier
        self.llm_service = llm_service

    async def execute(self, message_text: str, chat_id: int, user_context: UserContext) -> None:
        """Processes the text message using an LLM and sends a response.

        Args:
            message_text: The text content of the user's message.
            chat_id: The ID of the chat where the message was sent.
            user_context: Dictionary holding user-specific data like language.
        """
        logger.info(f"Processing message for chat {chat_id}: '{message_text[:50]}...'")
        language = user_context.get("language", settings.DEFAULT_LANGUAGE)

        try:
            # Process message with LLM
            # Consider adding context (chat history, user info) if needed by LLM
            response_text = await self.llm_service.process_message(message_text, language)

            if response_text:
                await self.notifier.send_notification(chat_id, response_text, parse_mode="Markdown")
            else:
                logger.warning("LLM service returned empty response.")
                # Optionally send a generic "I can't answer" message

        except Exception as e:
            logger.error(f"Error processing message with LLM: {e}", exc_info=True)
            error_msg = (
                "Sorry, I couldn't process your request right now."
                if language == Language.ENGLISH
                else "Извините, я не смог обработать ваш запрос сейчас."
            )
            await self.notifier.send_notification(chat_id, error_msg, parse_mode=None)
