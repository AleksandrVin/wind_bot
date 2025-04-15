"""
Abstract interface for accessing Bot Statistics data.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

# Use Pydantic schemas for data transfer
from interfaces.web.schemas import BotStatsRead, BotStatsUpdate

# Forward reference for type hinting if needed, or import later
# from domain.models.stats import BotStats # If we create separate domain models
# For now, we'll assume repositories return the ORM model type


class AbstractStatsRepository(ABC):
    """Abstract base class for stats repositories."""

    @abstractmethod
    def get_latest_stats(self) -> Optional[BotStatsRead]:
        """Retrieve the most recent BotStats record as a DTO."""
        pass

    @abstractmethod
    def get_all_stats(self) -> List[BotStatsRead]:
        """Retrieve all BotStats records as DTOs, ordered by timestamp descending."""
        pass

    @abstractmethod
    def update_or_create_stats(self, update_data: BotStatsUpdate) -> BotStatsRead:
        """Update the latest stats record or create a new one if none exists.

        Args:
            update_data: A Pydantic model containing fields to update/increment.

        Returns:
            The updated or newly created BotStats record as a DTO.
        """
        pass
