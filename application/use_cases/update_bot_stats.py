"""
Use Case: Update bot statistics.
"""

import logging
from typing import Any, Dict

from application.interfaces.stats_repository import AbstractStatsRepository
from interfaces.web.models import BotStats  # Assuming repo returns ORM model

logger = logging.getLogger(__name__)


class UpdateBotStatsUseCase:
    def __init__(self, repo: AbstractStatsRepository):
        self.repo = repo

    def execute(self, update_data: Dict[str, Any]) -> BotStats:
        """Updates or creates bot statistics.

        Args:
            update_data: Dictionary containing fields to update.

        Returns:
            The updated/created BotStats object.

        Raises:
            Exception: If the repository fails to update/create stats.
        """
        logger.info(f"Executing UpdateBotStatsUseCase with data: {update_data}")
        try:
            updated_stats = self.repo.update_or_create_stats(update_data)
            return updated_stats
        except Exception as e:
            logger.error(f"UpdateBotStatsUseCase failed: {e}", exc_info=True)
            raise
