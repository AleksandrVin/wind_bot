"""
Redis implementation of the Alert State repository.
Stores a flag for each chat indicating if an alert was sent today.
"""

import logging
from datetime import date, timedelta

import redis

from application.interfaces.alert_state_repository import AbstractAlertStateRepository
from config import settings  # To get Redis URL

logger = logging.getLogger(__name__)


class RedisAlertStateRepository(AbstractAlertStateRepository):
    """Uses Redis to store the alert-sent-today flag for each chat.

    Keys are like: alert_sent:{chat_id}:{YYYY-MM-DD}
    Values are simple flags (e.g., "1").
    Keys expire after 24 hours.
    """

    def __init__(self, redis_url: str = settings.REDIS_URL):
        try:
            self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()  # Check connection
            logger.info(f"RedisAlertStateRepository connected to {redis_url}")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Redis at {redis_url}: {e}")
            # Decide how to handle: raise error, use fallback, etc.
            # For now, let it fail hard if Redis is unavailable.
            raise
        except Exception as e:
            logger.error(f"Error initializing RedisAlertStateRepository: {e}")
            raise

    def _get_key(self, chat_id: int, alert_date: date) -> str:
        """Generates the Redis key for a given chat and date."""
        return f"alert_sent:{chat_id}:{alert_date.isoformat()}"

    def was_alert_sent_today(self, chat_id: int) -> bool:
        today = date.today()
        key = self._get_key(chat_id, today)
        try:
            exists = self.redis_client.exists(key)
            logger.debug(f"Checked alert state for chat {chat_id} (key: {key}): Exists={bool(exists)}")
            return bool(exists)
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error checking alert state for chat {chat_id}: {e}")
            return False  # Fail safe: assume not sent if Redis fails

    def mark_alert_sent(self, chat_id: int, alert_date: date = None) -> None:
        if alert_date is None:
            alert_date = date.today()
        key = self._get_key(chat_id, alert_date)
        try:
            # Set the key with an expiration of 24 hours (in seconds)
            # Use SET with EX option for atomicity
            self.redis_client.set(key, "1", ex=int(timedelta(hours=24).total_seconds()))
            logger.info(f"Marked alert sent for chat {chat_id} for date {alert_date} (key: {key})")
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error marking alert sent for chat {chat_id}: {e}")
            # Decide if failure here is critical. Logging might be sufficient.
