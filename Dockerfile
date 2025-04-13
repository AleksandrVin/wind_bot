# Use a slim Python base image
FROM ghcr.io/astral-sh/uv:python3.13-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy dependency definition file
COPY pyproject.toml ./

# Install dependencies using uv from pyproject.toml in the current directory
RUN uv pip install --no-cache --system .

# Copy project code
COPY . .

# Create instance directory needed by the app
RUN mkdir instance

# Expose the port the web server runs on
EXPOSE 5000

# Default command (can be overridden in docker-compose)
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "main:app"] 
