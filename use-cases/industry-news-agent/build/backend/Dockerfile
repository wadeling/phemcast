# Backend Dockerfile for Industry News Agent
# Based on Python 3.12 for the FastAPI backend

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Change apt source to Aliyun for faster download
RUN echo "deb https://mirrors.aliyun.com/debian/ bookworm main" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main" >> /etc/apt/sources.list

# Install system dependencies and fonts
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY ./src/ ./src/
COPY ./requirements.txt ./app_requirements.txt
COPY init_invite_codes.py .

# Change pip source to Aliyun for faster download
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com
    
# Install application dependencies
RUN pip install --no-cache-dir -r app_requirements.txt

# Create necessary directories
RUN mkdir -p /app/reports /app/logs

# Configure fonts for ReportLab
RUN mkdir -p /app/fonts && \
    echo "import os" > /app/fonts/__init__.py && \
    echo "import platform" >> /app/fonts/__init__.py && \
    echo "def get_font_paths():" >> /app/fonts/__init__.py && \
    echo "    paths = [" >> /app/fonts/__init__.py && \
    echo "        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'," >> /app/fonts/__init__.py && \
    echo "        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'," >> /app/fonts/__init__.py && \
    echo "        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'," >> /app/fonts/__init__.py && \
    echo "    ]" >> /app/fonts/__init__.py && \
    echo "    return [p for p in paths if os.path.exists(p)]" >> /app/fonts/__init__.py

# Set permissions
RUN chmod -R 755 /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "src.web_interface:app", "--host", "0.0.0.0", "--port", "8000"]
