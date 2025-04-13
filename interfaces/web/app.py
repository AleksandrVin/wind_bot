"""
Flask web interface for managing and monitoring the wind sports Telegram bot.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from config import settings
from interfaces.web.models import db, BotStats, WeatherLog

logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__, 
            template_folder='../../templates',
            static_folder='../../static')

app.secret_key = os.environ.get("SESSION_SECRET", settings.SESSION_SECRET)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URI
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = settings.DATABASE_ENGINE_OPTIONS

# Initialize the app with the extension
db.init_app(app)


@app.route("/")
def index():
    """Render the home page."""
    try:
        # Get the latest stats
        stats = BotStats.query.order_by(BotStats.timestamp.desc()).first()
        
        # Get recent weather logs (last 24 hours)
        recent_weather = WeatherLog.query.filter(
            WeatherLog.timestamp >= datetime.now() - timedelta(days=1)
        ).order_by(WeatherLog.timestamp.desc()).limit(10).all()
        
        return render_template(
            "index.html",
            stats=stats,
            recent_weather=recent_weather
        )
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return render_template("index.html", error=str(e))


@app.route("/stats")
def stats():
    """Render the statistics page."""
    try:
        # Get all stats ordered by timestamp
        all_stats = BotStats.query.order_by(BotStats.timestamp.desc()).all()
        
        # Calculate daily stats (simplified version)
        daily_stats = []
        weather_logs = WeatherLog.query.order_by(WeatherLog.timestamp.desc()).all()
        
        return render_template(
            "stats.html",
            all_stats=all_stats,
            daily_stats=daily_stats,
            weather_logs=weather_logs
        )
    except Exception as e:
        logger.error(f"Error rendering stats page: {e}")
        return render_template("stats.html", error=str(e))


@app.route("/api/add_weather_log", methods=["POST"])
def add_weather_log():
    """API endpoint to add a weather log entry."""
    try:
        data = request.json
        
        weather_log = WeatherLog(
            temperature=data.get("temperature", 0),
            wind_speed_knots=data.get("wind_speed_knots", 0),
            wind_speed_ms=data.get("wind_speed_ms", 0),
            has_rain=data.get("has_rain", False)
        )
        
        db.session.add(weather_log)
        db.session.commit()
        
        return jsonify({"message": "Weather log added successfully"}), 201
    except Exception as e:
        logger.error(f"Error adding weather log: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/update_stats", methods=["POST"])
def update_stats():
    """API endpoint to update bot statistics."""
    try:
        data = request.json
        
        # Get the latest stats or create new if none exist
        stats = BotStats.query.order_by(BotStats.timestamp.desc()).first()
        if not stats:
            stats = BotStats()
            db.session.add(stats)
        
        # Update the stats based on the data received
        if "messages_processed" in data:
            stats.messages_processed += data["messages_processed"]
        if "weather_commands" in data:
            stats.weather_commands += data["weather_commands"]
        if "forecast_commands" in data:
            stats.forecast_commands += data["forecast_commands"]
        if "wind_commands" in data:
            stats.wind_commands += data["wind_commands"]
        if "alerts_sent" in data:
            stats.alerts_sent += data["alerts_sent"]
        if "active_users" in data:
            stats.active_users = data["active_users"]
        
        db.session.commit()
        
        return jsonify({"message": "Stats updated successfully"}), 201
    except Exception as e:
        logger.error(f"Error updating stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/get_recent_weather", methods=["GET"])
def get_recent_weather():
    """API endpoint to get recent weather data."""
    try:
        hours = request.args.get("hours", 24, type=int)
        
        # Get weather logs for the specified time period
        logs = WeatherLog.query.filter(
            WeatherLog.timestamp >= datetime.now() - timedelta(hours=hours)
        ).order_by(WeatherLog.timestamp.asc()).all()
        
        data = []
        for log in logs:
            data.append({
                "timestamp": log.timestamp.isoformat(),
                "temperature": log.temperature,
                "wind_speed_knots": log.wind_speed_knots,
                "wind_speed_ms": log.wind_speed_ms,
                "has_rain": log.has_rain
            })
        
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting recent weather data: {e}")
        return jsonify({"error": str(e)}), 500

# Create database tables on startup
with app.app_context():
    db.create_all()
    
    # Initialize stats if none exist
    if BotStats.query.count() == 0:
        stats = BotStats()
        db.session.add(stats)
        db.session.commit()
        logger.info("Initialized default bot stats")