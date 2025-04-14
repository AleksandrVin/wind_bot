# Wind Sports Telegram Bot

A Telegram bot for kitesurfing and windsurfing enthusiasts that provides weather updates, alerts for optimal wind conditions, and daily forecasts.

## Technologies Used

- **Backend**: Python, FastAPI, Celery, Redis
- **Database**: 
  - **Docker**: PostgreSQL with SQLAlchemy
  - **Local Dev**: SQLite with SQLAlchemy (fallback)
- **APIs**: OpenWeather API, Telegram Bot API
- **AI/ML**: LangChain, OpenAI
- **Frontend**: Bootstrap, Chart.js, Jinja2 (via FastAPI)

## Project Structure (DDD Architecture)

- `/application` - Application layer (use cases, interfaces)
- `/domain` - Domain layer (entities, domain models, core services)
- `/infrastructure` - Infrastructure layer (external services, persistence, database setup)
- `/interfaces` - Interface adapters:
  - `/web` - FastAPI web interface (`app.py`), database models (`models.py`), API schemas (`schemas.py`)
  - `/telegram` - Telegram bot interface (`bot_controller.py`)
- `/templates` - Jinja2 templates for the web UI
- `/static` - Static assets (CSS, JS) for the web UI

## Getting Started

### Native Setup

1.  Set up environment variables in `.env`:
    ```bash
    # Required for Docker and Native setup
    POSTGRES_USER=your_postgres_user
    POSTGRES_PASSWORD=your_postgres_password
    POSTGRES_DB=wind_bot_db # Default DB name
    DATABASE_URL=postgresql+psycopg2://your_postgres_user:your_postgres_password@db:5432/wind_bot_db # Use 'db' as hostname for Docker
    CELERY_BROKER_URL=redis://redis:6379/0 # Use 'redis' as hostname for Docker
    CELERY_RESULT_BACKEND=redis://redis:6379/1 # Use 'redis' as hostname for Docker
    TELEGRAM_BOT_TOKEN=your_telegram_token
    OPENWEATHER_API_KEY=your_openweather_key
    OPENAI_API_KEY=your_openai_key
    LANGSMITH_API_KEY=your_langsmith_key
    WEB_API_URL=http://web:5000/api # Use 'web' hostname for Docker, http://localhost:5000/api for native
    ```
    *Note: For native setup without Docker, adjust `DATABASE_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, and `WEB_API_URL` to point to `localhost` or your specific service addresses if they are running outside Docker.* 

2.  Ensure you have Python >=3.11 and install dependencies (preferably using `uv`):
    ```bash
    pip install uv
    uv sync  # Installs dependencies based on pyproject.toml and uv.lock
    ```

3.  Run database initialization (first time or after model changes):
    ```bash
    python infrastructure/persistence/init_db.py
    ```

4.  Start the application (only web server):
    ```bash
    # For local development using the root app.py runner
    python app.py 
    # Or directly using uvicorn:
    # uvicorn interfaces.web.app:app --host 0.0.0.0 --port 5000 --reload
    ```
    *Note: The old `start.py` script is still configured to run only the web server via Uvicorn.* 
    *To run the full application (web, bot, celery), use Docker Compose.* 

### Docker Compose Setup (Recommended)

1.  **Ensure Docker and Docker Compose are installed.**
2.  **Create a `.env` file** in the project root directory. Copy the example from the "Native Setup" section above, ensuring the hostnames for `DATABASE_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, and `WEB_API_URL` are set correctly for Docker (`db`, `redis`, `web`).
3.  **Build and run the services:**
    ```bash
    docker compose build
    docker compose up -d
    ```
    This command will:
    - Build the application Docker image based on `Dockerfile`.
    - Run the `db_init` service to initialize the database schema.
    - Start containers for the FastAPI web server (Uvicorn), Telegram bot, Celery worker, Celery beat, PostgreSQL database, and Redis.
    - Run the services in detached mode (`-d`).

4.  **Accessing Services:**
    - Web Interface: `http://localhost:5000`
    - API Docs (Swagger): `http://localhost:5000/docs`
    - API Docs (ReDoc): `http://localhost:5000/redoc`
    - Database (if needed for direct access): `localhost:5432`
    - Redis (if needed for direct access): `localhost:6379`

5.  **Stopping Services:**
    ```bash
    docker compose down
    ```
    This will stop and remove the containers.

## Features

- Real-time weather monitoring
- Wind speed alerts
- Daily weather forecasts
- Web dashboard with statistics (FastAPI with Jinja2)
- RESTful API for stats and weather logs (FastAPI)
- Natural language processing for weather queries
- Unit conversion (m/s to knots)

## Configuration

Core settings can be modified in `config.py`, including:

- API Keys (Telegram, OpenWeather, OpenAI, LangSmith)
- Database and Redis connection URLs
- Wind speed thresholds
- Alert timing
- Default location coordinates
- Language preferences (EN/RU)
- Internal Web API URL (`WEB_API_URL`)

## Development

The project follows Domain-Driven Design principles with clear separation of concerns. Core business logic is isolated in the domain layer, while external integrations are handled in the infrastructure layer. The web interface is built using FastAPI, providing asynchronous capabilities and automatic API documentation.
