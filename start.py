#!/usr/bin/env python
"""
Startup script for the web server, Telegram bot, and Celery worker
"""
import asyncio
import logging
import os
import threading
import sys
import time

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Import settings
try:
    from config import settings
except Exception as e:
    logger.error(f"Error importing settings: {e}")

def start_web_server():
    """Start the Flask web server"""
    logger.info("Starting Web Server...")
    os.system("gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app")

def start_telegram_bot():
    """Start the Telegram bot"""
    logger.info("Starting Telegram Bot...")
    os.system("python run_bot.py")

def start_celery_worker():
    """Start the Celery worker for background tasks"""
    logger.info("Starting Celery Worker...")
    os.system("celery -A tasks worker --loglevel=info --concurrency=1")

def start_celery_beat():
    """Start the Celery beat scheduler for periodic tasks"""
    logger.info("Starting Celery Beat Scheduler...")
    os.system("celery -A tasks beat --loglevel=info")

async def main():
    """Main function to start all services"""
    logger.info("Starting all services...")
    
    # Ensure instance directory exists for SQLite database
    os.makedirs("instance", exist_ok=True)
    logger.info("Ensured instance directory exists")
    
    # Start the web server in a separate thread
    web_thread = threading.Thread(target=start_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # Sleep to allow web server to start
    await asyncio.sleep(3)
    
    # Start the Telegram bot
    bot_thread = threading.Thread(target=start_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    logger.info("All services started!")
    
    # Keep the main thread running
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down all services...")
        sys.exit(0)