"""
Main entry point for the wind sports Telegram bot application.
"""

import logging

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import the web interface
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
