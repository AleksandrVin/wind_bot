"""
Use Case: Update bot statistics.
"""

import logging

from application.interfaces.stats_repository import AbstractStatsRepository
from interfaces.web.schemas import BotStatsRead, BotStatsUpdate

logger = logging.getLogger(__name__)


class UpdateBotStatsUseCase:
    def __init__(self, repo: AbstractStatsRepository):
        self.repo = repo

    def execute(self, update_data: BotStatsUpdate) -> BotStatsRead:
        """Updates or creates bot statistics.

        Args:
            update_data: Pydantic model containing fields to update.

        Returns:
            The updated/created BotStats DTO.

        Raises:
            Exception: If the repository fails to update/create stats.
        """
        logger.info(f"Executing UpdateBotStatsUseCase with data: {update_data}")
        try:
            updated_stats_dto = self.repo.update_or_create_stats(update_data)
            return updated_stats_dto
        except Exception as e:
            logger.error(f"UpdateBotStatsUseCase failed: {e}", exc_info=True)
            raise
