# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set metadata
LABEL maintainer="OBS-TV-Animator"
LABEL description="WebSocket-enabled server for Smart TV animations and video playback"
LABEL version="2.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies including FFmpeg for video thumbnails and Playwright browser deps
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    ffmpeg \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright (but not browsers yet)
RUN pip install --no-cache-dir playwright

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/animations /app/videos /app/data /app/data/config /app/data/logs /app/data/thumbnails && \
    chmod -R 755 /app/animations /app/videos /app/data

# Create non-root user for security  
RUN groupadd -r appuser && useradd -r -g appuser -m appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Install Playwright browsers as the correct user
RUN playwright install chromium

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]

# Start the application
CMD ["python", "app.py"]