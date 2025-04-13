# Wind Sports Telegram Bot

A Telegram bot for kitesurfing and windsurfing enthusiasts that provides weather updates, alerts for optimal wind conditions, and daily forecasts.

## Technologies Used

- **Backend**: Python, Flask, Celery, Redis
- **Database**: 
  - **Docker**: PostgreSQL with SQLAlchemy
  - **Local Dev**: SQLite with SQLAlchemy (fallback)
- **APIs**: OpenWeather API, Telegram Bot API
- **AI/ML**: LangChain, OpenAI
- **Frontend**: Bootstrap, Chart.js

## Project Structure (DDD Architecture)

- `/application` - Application layer (use cases, interfaces)
- `/domain` - Domain layer (entities, models, core services)
- `/infrastructure` - Infrastructure layer (external services, persistence)
- `/interfaces` - Interface adapters (web, CLI, Telegram)

## Getting Started

### Native Setup

1.  Set up environment variables in `.env`:
    ```bash
    # Required for Docker and Native setup
    POSTGRES_USER=your_postgres_user
    POSTGRES_PASSWORD=your_postgres_password
    POSTGRES_DB=your_postgres_db
    DATABASE_URL=postgresql+psycopg2://your_postgres_user:your_postgres_password@db:5432/your_postgres_db # Use 'db' as hostname for Docker
    CELERY_BROKER_URL=redis://redis:6379/0 # Use 'redis' as hostname for Docker
    CELERY_RESULT_BACKEND=redis://redis:6379/1 # Use 'redis' as hostname for Docker
    TELEGRAM_BOT_TOKEN=your_telegram_token
    OPENWEATHER_API_KEY=your_openweather_key
    OPENAI_API_KEY=your_openai_key
    LANGSMITH_API_KEY=your_langsmith_key
    ```
    *Note: For native setup without Docker, adjust `DATABASE_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` to point to `localhost` or your specific service addresses if they are running outside Docker.* 

2.  Ensure you have Python >=3.11 and install dependencies (preferably using `uv`):
    ```bash
    pip install uv
    uv sync  # Or sync with pyproject.toml if preferred
    ```

3.  Start the application:
    ```bash
    python start.py
    ```
    This will launch:
    - Web interface on port 5000
    - Telegram bot
    - Celery worker for background tasks

### Docker Compose Setup (Recommended)

1.  **Ensure Docker and Docker Compose are installed.**
2.  **Create a `.env` file** in the project root directory. Copy the example from the "Native Setup" section above, ensuring the hostnames for `DATABASE_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` are set to `db` and `redis` respectively, as they will run within the Docker network.
3.  **Build and run the services:**
    ```bash
    docker compose build
    docker compose up -d
    ```
    This command will:
    - Build the application Docker image based on `Dockerfile`.
    - Start containers for the web server, Telegram bot, Celery worker, Celery beat, PostgreSQL database, and Redis.
    - Run the services in detached mode (`-d`).

4.  **Accessing Services:**
    - Web Interface: `http://localhost:5000`
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
- Web dashboard with statistics
- Natural language processing for weather queries
- Unit conversion (m/s to knots)

## Configuration

Core settings can be modified in `config.py`, including:

- Wind speed thresholds
- Alert timing
- Default location coordinates
- Language preferences (EN/RU)

## Development

The project follows Domain-Driven Design principles with clear separation of concerns. Core business logic is isolated in the domain layer, while external integrations are handled in the infrastructure layer.
