"""
Main entry point for the Uvicorn server.
Imports the FastAPI app instance from the interfaces.web.app module.
"""

import logging

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import the FastAPI app instance from its new location
from interfaces.web.app import app

# The Uvicorn server will look for this `app` variable.

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
