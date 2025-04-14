"""
Main entry point for running the FastAPI application locally using Uvicorn.
Imports the FastAPI app instance from the interfaces.web.app module.
"""

import logging

import uvicorn

# Import the FastAPI app instance from its new location
from interfaces.web.app import app

logger = logging.getLogger(__name__)

# The Uvicorn server will look for this `app` variable.

if __name__ == "__main__":
    # This block is for running the app directly with uvicorn for local development
    # In production, you'd run: uvicorn interfaces.web.app:app --host 0.0.0.0 --port 5000
    logger.info("Starting Uvicorn server for local development...")
    # Reference the app instance directly for uvicorn.run
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)
