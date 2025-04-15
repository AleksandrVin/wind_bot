"""
Abstract interface for managing the state of wind alerts.
"""

from abc import ABC, abstractmethod
from datetime import date


class AbstractAlertStateRepository(ABC):
    """Interface for checking and setting the wind alert state for a chat.

    This typically checks if an alert was already sent *today*.
    """

    @abstractmethod
    def was_alert_sent_today(self, chat_id: int) -> bool:
        """Check if an alert has already been sent to this chat today.

        Args:
            chat_id: The chat identifier.

        Returns:
            True if an alert was sent today, False otherwise.
        """
        pass

    @abstractmethod
    def mark_alert_sent(self, chat_id: int, alert_date: date = None) -> None:
        """Mark that an alert has been sent to this chat for a specific date.

        Args:
            chat_id: The chat identifier.
            alert_date: The date the alert was sent (defaults to today).
        """
        pass
