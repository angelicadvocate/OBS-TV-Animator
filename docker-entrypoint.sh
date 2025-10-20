#!/bin/bash
# Docker entrypoint script for OBS-TV-Animator

set -e

echo "===================================================================================="
echo "OBS-TV-Animator Docker Container Starting..."
echo "===================================================================================="
echo '  ____  ____   _____    _________      __            _   _ _____ __  __       _______ ____  _____  '
echo ' / __ \|  _ \ / ____|  |__   __\ \    / /      /\   | \ | |_   _|  \/  |   /\|__   __/ __ \|  __ \ '
echo '| |  | | |_) | (___ ______| |   \ \  / /_____ /  \  |  \| | | | | \  / |  /  \  | | | |  | | |__) |'
echo '| |  | |  _ < \___ \______| |    \ \/ /______/ /\ \ | . ` | | | | |\/| | / /\ \ | | | |  | |  _  / '
echo '| |__| | |_) |____) |     | |     \  /      / ____ \| |\  |_| |_| |  | |/ ____ \| | | |__| | | \ \ '
echo ' \____/|____/|_____/      |_|      \/      /_/    \_\_| \_|_____|_|  |_/_/    \_\_|  \____/|_|  \_\'
echo ""
echo "===================================================================================="

# Create directories if they don't exist
mkdir -p /app/animations /app/videos /app/data /app/logs

# Set permissions
chmod 755 /app/animations /app/videos /app/data /app/logs

# Check if required directories are mounted
if [ ! -d "/app/animations" ]; then
    echo "WARNING: /app/animations directory not found. Creating default..."
    mkdir -p /app/animations
fi

if [ ! -d "/app/videos" ]; then
    echo "WARNING: /app/videos directory not found. Creating default..."
    mkdir -p /app/videos
fi

# Initialize state file if it doesn't exist
if [ ! -f "/app/data/state.json" ]; then
    echo "Initializing state.json..."
    echo '{"current_animation": "anim1.html"}' > /app/data/state.json
fi

# Display startup information
echo "Docker Configuration:"
echo "  Port: ${PORT:-8080}"
echo "  Flask Environment: ${FLASK_ENV:-production}"
echo "  Python Version: $(python --version)"
echo ""
echo "Media Directories:"
echo "  Animations: $(find /app/animations -maxdepth 1 -type f ! -name '*.md' ! -name '*.txt' | wc -l) files"
echo "  Videos: $(find /app/videos -maxdepth 1 -type f ! -name '*.md' ! -name '*.txt' | wc -l) files"
echo ""
echo "Network Information:"
echo "  Container IP: $(hostname -i 2>/dev/null || echo 'Not available')"
echo "  Listening on: 0.0.0.0:${PORT:-8080}"
echo ""
echo "Access URLs:"
echo "  Smart TV/Display: http://[HOST_IP]:${PORT:-8080}"
echo "  WebSocket: ws://[HOST_IP]:${PORT:-8080}/socket.io/"
echo "  Management: http://[HOST_IP]:${PORT:-8080}/admin"
echo ""
echo "===================================================================================="

# Execute the main application
exec "$@"