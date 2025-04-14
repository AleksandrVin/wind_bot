"""
SQLAlchemy implementation of the Bot Statistics repository.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from application.interfaces.stats_repository import AbstractStatsRepository
from interfaces.web.models import BotStats  # Using the ORM model

logger = logging.getLogger(__name__)


class SqlStatsRepository(AbstractStatsRepository):
    """SQLAlchemy implementation for stats persistence."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_latest_stats(self) -> Optional[BotStats]:
        try:
            return self.db.query(BotStats).order_by(BotStats.timestamp.desc()).first()
        except Exception as e:
            logger.error(f"Error fetching latest stats: {e}", exc_info=True)
            return None

    def get_all_stats(self) -> List[BotStats]:
        try:
            return self.db.query(BotStats).order_by(BotStats.timestamp.desc()).all()
        except Exception as e:
            logger.error(f"Error fetching all stats: {e}", exc_info=True)
            return []

    def update_or_create_stats(self, update_data: Dict[str, Any]) -> BotStats:
        try:
            stats = self.get_latest_stats()
            if not stats:
                logger.info("No existing stats found, creating new record.")
                stats = BotStats()
                self.db.add(stats)

            logger.debug(f"Updating stats with data: {update_data}")
            for key, value in update_data.items():
                if value is not None and hasattr(stats, key):
                    current_value = getattr(stats, key)
                    if isinstance(current_value, (int, float)) and key != "active_users":
                        # Increment counters
                        new_value = current_value + value
                        setattr(stats, key, new_value)
                        logger.debug(f"Incremented {key}: {current_value} + {value} -> {new_value}")
                    else:
                        # Overwrite values (like active_users)
                        setattr(stats, key, value)
                        logger.debug(f"Set {key} to {value}")

            # Always update timestamp
            stats.timestamp = datetime.now(timezone.utc)
            logger.debug(f"Set timestamp to {stats.timestamp}")

            self.db.commit()
            self.db.refresh(stats)
            logger.info(f"Successfully updated/created stats record ID: {stats.id}")
            return stats
        except Exception as e:
            logger.error(f"Error updating/creating stats: {e}", exc_info=True)
            self.db.rollback()
            # Re-raise the exception to be handled by the use case/endpoint
            raise
