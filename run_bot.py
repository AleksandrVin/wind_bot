#!/usr/bin/env python
"""
Main script to run the Telegram bot.
"""

import asyncio
import logging

from config import settings
from interfaces.telegram.bot_controller import TelegramBotController

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and run the bot."""
    logger.info("Initializing bot controller...")
    bot_controller = TelegramBotController(token=settings.TELEGRAM_TOKEN)

    try:
        logger.info("Starting bot...")
        await bot_controller.start()
        # Keep the script running indefinitely
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping bot...")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        logger.info("Shutting down bot...")
        await bot_controller.stop()
        logger.info("Bot shut down complete.")


if __name__ == "__main__":
    asyncio.run(main())
