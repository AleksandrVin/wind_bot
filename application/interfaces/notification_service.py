"""
Abstract interface for sending notifications.
"""

from abc import ABC, abstractmethod


class AbstractNotificationService(ABC):
    """Interface for sending notifications to users (e.g., via Telegram)."""

    @abstractmethod
    async def send_notification(self, target_id: int, message: str, parse_mode: str = None) -> bool:
        """Send a notification message.

        Args:
            target_id: The identifier of the recipient (e.g., Telegram chat_id).
            message: The message content.
            parse_mode: Optional formatting mode (e.g., 'Markdown', 'HTML').

        Returns:
            True if sending was successful (or successfully queued), False otherwise.
        """
        pass
