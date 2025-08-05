FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Copy pyproject.toml for dependencies
COPY pyproject.toml ./

# Install Python dependencies from pyproject.toml
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN adduser --disabled-password --gecos '' jarvis-ai && \
    chown -R jarvis-ai:jarvis-ai /app
USER jarvis-ai

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 