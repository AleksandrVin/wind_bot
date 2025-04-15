"""
Infrastructure implementation for sending notifications via Telegram.
"""

import logging

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from application.interfaces.notification_service import AbstractNotificationService
from config import settings  # To get the bot token

logger = logging.getLogger(__name__)


class TelegramNotificationService(AbstractNotificationService):
    """Sends notifications using the python-telegram-bot library."""

    def __init__(self, token: str = settings.TELEGRAM_TOKEN):
        """Initialize with bot token."""
        if not token:
            raise ValueError("Telegram bot token is required.")
        self.bot = Bot(token=token)
        logger.info("TelegramNotificationService initialized.")

    async def send_notification(self, target_id: int, message: str, parse_mode: str = ParseMode.MARKDOWN) -> bool:
        """Send a notification message via Telegram."""
        try:
            await self.bot.send_message(chat_id=target_id, text=message, parse_mode=parse_mode)
            logger.info(f"Successfully sent notification to {target_id}")
            return True
        except TelegramError as e:
            logger.error(f"Telegram error sending notification to {target_id}: {e}")
            # Specific error handling (e.g., bot blocked)
            if "bot was blocked by the user" in str(e):
                logger.warning(f"Bot blocked by user in chat {target_id}.")
                # Potentially trigger an action like removing the user/chat ID
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending notification to {target_id}: {e}", exc_info=True)
            return False
