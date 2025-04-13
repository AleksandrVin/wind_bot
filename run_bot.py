#!/usr/bin/env python
"""
Run script for the Wind Sports Telegram Bot
"""

import asyncio
import logging
import os
import sys

from config import settings
from interfaces.telegram.bot_controller import TelegramBotController

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot"""
    logger.info("Starting the Wind Sports Telegram Bot...")

    # Check for valid Telegram token
    if not settings.TELEGRAM_TOKEN:
        logger.error("No Telegram Bot token provided. Set the TELEGRAM_TOKEN environment variable.")
        sys.exit(1)

    # Initialize the bot controller
    bot = TelegramBotController(token=settings.TELEGRAM_TOKEN)

    try:
        # Start the bot
        await bot.start()

        # Keep the bot running until interrupted
        stop_signal = asyncio.Future()
        await stop_signal
    except asyncio.CancelledError:
        pass
    finally:
        # Ensure we close gracefully
        await bot.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
        sys.exit(0)
