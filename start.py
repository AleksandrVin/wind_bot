#!/usr/bin/env python
"""
Startup script for the web server
"""

import asyncio
import logging
import os
import sys
import threading

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import settings
try:
    pass
except Exception as e:
    logger.error(f"Error importing settings: {e}")


def start_web_server():
    """Start the FastAPI web server using Uvicorn"""
    logger.info("Starting Web Server with Uvicorn...")
    # Use Uvicorn to run the app defined in interfaces/web/app.py
    os.system("uvicorn interfaces.web.app:app --host 0.0.0.0 --port 5000 --reload")


async def main():
    """Main function to start the web server"""
    logger.info("Starting web server only...")

    # Ensure instance directory exists for SQLite database (as fallback)
    # os.makedirs("instance", exist_ok=True) # Keep if SQLite fallback needs it
    # logger.info("Ensured instance directory exists")

    # Start the web server in a separate thread
    web_thread = threading.Thread(target=start_web_server)
    web_thread.daemon = True
    web_thread.start()

    logger.info("Web server started!")

    # Keep the main thread running
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down web server...")
        sys.exit(0)
