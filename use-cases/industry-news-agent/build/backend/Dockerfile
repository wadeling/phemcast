# Backend Dockerfile for Industry News Agent
# Based on Python 3.12 for the FastAPI backend

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY ./src/ ./src/
COPY ./requirements.txt ./app_requirements.txt

# Install application dependencies
RUN pip install --no-cache-dir -r app_requirements.txt

# Create necessary directories
RUN mkdir -p /app/reports /app/logs

# Set permissions
RUN chmod -R 755 /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "src.web_interface:app", "--host", "0.0.0.0", "--port", "8000"]
