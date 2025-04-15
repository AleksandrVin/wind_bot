"""
SQLAlchemy implementation of the Stats Repository.
Uses SQLModel for models and session management.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession  # Import AsyncSession

from application.interfaces.stats_repository import AbstractStatsRepository
from domain.models.stats import BotStats
from interfaces.web.schemas import (  # Assuming schemas are still useful
    BotStatsRead,
    BotStatsUpdate,
)

logger = logging.getLogger(__name__)


class SqlStatsRepository(AbstractStatsRepository):
    """SQLAlchemy repository for bot statistics."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_stats(self) -> Optional[BotStatsRead]:
        """Retrieve the most recent BotStats record asynchronously."""
        try:
            statement = select(BotStats).order_by(BotStats.timestamp.desc()).limit(1)
            result = await self.session.exec(statement)
            db_stats = result.first()
            if db_stats:
                return BotStatsRead.from_orm(db_stats)
            return None
        except Exception as e:
            logger.error(f"Error retrieving latest stats: {e}", exc_info=True)
            # Consider raising a custom repository exception
            return None

    async def get_all_stats(self) -> List[BotStatsRead]:
        """Retrieve all BotStats records asynchronously."""
        try:
            statement = select(BotStats).order_by(BotStats.timestamp.desc())
            results = await self.session.exec(statement)
            db_stats_list = results.all()
            return [BotStatsRead.from_orm(stats) for stats in db_stats_list]
        except Exception as e:
            logger.error(f"Error retrieving all stats: {e}", exc_info=True)
            return []

    async def update_or_create_stats(self, stats_update: BotStatsUpdate) -> Optional[BotStatsRead]:
        """Update existing stats for today or create a new record asynchronously."""
        today = datetime.utcnow().date()
        try:
            # Check if stats for today already exist
            statement = select(BotStats).where(BotStats.date == today)
            result = await self.session.exec(statement)
            db_stats = result.first()

            if db_stats:
                # Update existing record
                logger.debug(f"Updating stats for date: {today}")
                update_data = stats_update.model_dump(exclude_unset=True)
                for key, value in update_data.items():
                    if value is not None:
                        current_value = getattr(db_stats, key)
                        setattr(db_stats, key, (current_value or 0) + value)
                db_stats.timestamp = datetime.utcnow()  # Update timestamp
            else:
                # Create new record
                logger.debug(f"Creating new stats record for date: {today}")
                db_stats = BotStats(
                    date=today,
                    timestamp=datetime.utcnow(),
                    **stats_update.model_dump(),  # Pass all fields from update DTO
                )

            self.session.add(db_stats)
            await self.session.commit()
            await self.session.refresh(db_stats)
            logger.info(f"Successfully {'updated' if update_data else 'created'} stats for {today}")
            return BotStatsRead.from_orm(db_stats)

        except Exception as e:
            logger.error(f"Error updating or creating stats for date {today}: {e}", exc_info=True)
            await self.session.rollback()  # Rollback on error
            return None
