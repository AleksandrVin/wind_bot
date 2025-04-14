"""
Abstract interface for accessing Bot Statistics data.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# Forward reference for type hinting if needed, or import later
# from domain.models.stats import BotStats # If we create separate domain models
# For now, we'll assume repositories return the ORM model type
from interfaces.web.models import BotStats


class AbstractStatsRepository(ABC):
    """Abstract base class for stats repositories."""

    @abstractmethod
    def get_latest_stats(self) -> Optional[BotStats]:
        """Retrieve the most recent BotStats record."""
        pass

    @abstractmethod
    def get_all_stats(self) -> List[BotStats]:
        """Retrieve all BotStats records, ordered by timestamp descending."""
        pass

    @abstractmethod
    def update_or_create_stats(self, update_data: Dict[str, Any]) -> BotStats:
        """Update the latest stats record or create a new one if none exists.

        Args:
            update_data: A dictionary containing fields to update/increment.
                         Keys should match BotStats attributes.
                         Values for counters will be added to the existing value.
                         'active_users' will overwrite the existing value.

        Returns:
            The updated or newly created BotStats record.
        """
        pass
