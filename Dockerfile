# Use a slim Python base image
FROM ghcr.io/astral-sh/uv:python3.11-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ADD . /app

# Set work directory
WORKDIR /app

# Install dependencies using uv from pyproject.toml in the current directory
RUN uv sync --frozen

# Expose the port the web server runs on
EXPOSE 5000

# Default command (can be overridden in docker-compose)
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "main:app"] 
