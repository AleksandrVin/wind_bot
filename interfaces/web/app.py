"""
FastAPI web interface for managing and monitoring the wind sports Telegram bot.
"""

import logging
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from application.use_cases.add_weather_log import AddWeatherLogUseCase
from application.use_cases.get_statistics import GetStatisticsUseCase
from application.use_cases.update_bot_stats import UpdateBotStatsUseCase

# Adjust imports to be relative to the project root or use absolute paths
from config import settings
from infrastructure.persistence.database import get_db
from infrastructure.persistence.sql_stats_repository import SqlStatsRepository
from infrastructure.persistence.sql_weather_log_repository import SqlWeatherLogRepository
from infrastructure.weather.openweather_service import OpenWeatherService

# ORM models are now here:
from interfaces.web import schemas  # API Schemas (Pydantic models)

logger = logging.getLogger(__name__)

# --- Dependency Injection Setup --- #


def get_stats_repo(db: Session = Depends(get_db)) -> SqlStatsRepository:
    return SqlStatsRepository(db)


def get_weather_log_repo(db: Session = Depends(get_db)) -> SqlWeatherLogRepository:
    return SqlWeatherLogRepository(db)


# --- FastAPI App Setup --- #

app = FastAPI(title="Wind Bot Web UI")

# Mount static files (CSS, JS) - relative to project root
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates - relative to project root
templates = Jinja2Templates(directory="templates")

# Initialize the weather service
weather_service = OpenWeatherService(
    api_key=settings.OPENWEATHER_API_KEY, latitude=settings.LATITUDE, longitude=settings.LONGITUDE
)

# --- FastAPI Path Operations (Routes) --- #


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    stats_repo: SqlStatsRepository = Depends(get_stats_repo),
    weather_repo: SqlWeatherLogRepository = Depends(get_weather_log_repo),
):
    """Render the home page."""
    error_message = None
    try:
        use_case = GetStatisticsUseCase(stats_repo, weather_repo)
        latest_stats, recent_logs = use_case.execute_dashboard()

        current_weather = weather_service.get_current_weather()
        weather_condition = ""
        if current_weather and current_weather.weather_conditions:
            weather_condition = current_weather.weather_conditions[0].main

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "stats": latest_stats,
                "current_weather": current_weather,
                "weather_condition": weather_condition,
                "weather_logs": recent_logs,
                "config": settings,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering index page: {e}", exc_info=True)
        error_message = "Failed to load dashboard data."  # User-friendly error
        return templates.TemplateResponse("index.html", {"request": request, "error": error_message})


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(
    request: Request,
    stats_repo: SqlStatsRepository = Depends(get_stats_repo),
    weather_repo: SqlWeatherLogRepository = Depends(get_weather_log_repo),
):
    """Render the statistics page."""
    error_message = None
    try:
        use_case = GetStatisticsUseCase(stats_repo, weather_repo)
        all_stats, weather_logs = use_case.execute_stats_page()
        latest_stats = all_stats[0] if all_stats else None

        return templates.TemplateResponse(
            "stats.html",
            {
                "request": request,
                "all_stats": all_stats,
                "latest_stats": latest_stats,
                "stats_data": all_stats[:20],  # Pass limited data for charts
                "weather_logs": weather_logs[:50],  # Limit logs displayed
            },
        )
    except Exception as e:
        logger.error(f"Error rendering stats page: {e}", exc_info=True)
        error_message = "Failed to load statistics data."
        return templates.TemplateResponse("stats.html", {"request": request, "error": error_message})


@app.post("/api/add_weather_log", response_model=schemas.WeatherLogRead, status_code=201)
async def add_weather_log(
    log_data: schemas.WeatherLogCreate, weather_repo: SqlWeatherLogRepository = Depends(get_weather_log_repo)
):
    """API endpoint to add a weather log entry."""
    try:
        use_case = AddWeatherLogUseCase(weather_repo)
        # Pass the Pydantic model dict to the use case
        created_log = use_case.execute(log_data.model_dump())
        # FastAPI will automatically convert the ORM model to the response_model
        return created_log
    except Exception:
        # Error already logged in use case/repo
        raise HTTPException(status_code=500, detail="Failed to add weather log.")


@app.post("/api/update_stats", response_model=schemas.BotStatsRead, status_code=200)
async def update_stats(stats_update: schemas.BotStatsUpdate, stats_repo: SqlStatsRepository = Depends(get_stats_repo)):
    """API endpoint to update bot statistics."""
    try:
        use_case = UpdateBotStatsUseCase(stats_repo)
        # Pass the Pydantic model dict (excluding unset fields) to the use case
        updated_stats = use_case.execute(stats_update.model_dump(exclude_unset=True))
        return updated_stats
    except Exception:
        # Error already logged in use case/repo
        raise HTTPException(status_code=500, detail="Failed to update bot statistics.")


@app.get("/api/get_recent_weather", response_model=List[schemas.WeatherLogRead])
async def get_recent_weather(hours: int = 24, weather_repo: SqlWeatherLogRepository = Depends(get_weather_log_repo)):
    """API endpoint to get recent weather data."""
    try:
        use_case = GetStatisticsUseCase(stats_repo=None, weather_repo=weather_repo)  # Stats repo not needed here
        logs = use_case.execute_recent_weather(hours=hours)
        return logs
    except Exception:
        # Error already logged in use case/repo
        raise HTTPException(status_code=500, detail="Failed to retrieve recent weather data.")


# Note: The __main__ block for uvicorn.run is removed
# It should only be in the main entrypoint script (e.g., root app.py or main.py)
