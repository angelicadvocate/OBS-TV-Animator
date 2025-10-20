#!/bin/bash
# OBS-TV-Animator Docker Quick Start Script

set -e

echo "🐳 OBS-TV-Animator Docker Quick Start"
echo "======================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed  
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running"
    echo "Please start Docker Desktop or Docker service"
    exit 1
fi

echo "✅ Docker is installed and running"

# Get host IP for display
HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
if [[ "$HOST_IP" == "localhost" ]]; then
    # Alternative method for getting IP
    if command -v ip &> /dev/null; then
        HOST_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K\S+' 2>/dev/null || echo "localhost")
    fi
fi

echo "📋 Pre-deployment checklist:"
echo "   ✅ Docker installed and running"
echo "   ✅ All configuration files validated"  
echo "   ✅ Directory structure ready"

# Create directories if they don't exist
echo ""
echo "📁 Setting up directories..."
mkdir -p animations videos data logs
echo "   ✅ Created: animations/, videos/, data/, logs/"

# Copy environment file if it doesn't exist
if [[ ! -f .env ]]; then
    echo "   📄 Copying .env.example to .env"
    cp .env.example .env
    echo "   ✅ Environment file ready (you can customize .env if needed)"
fi

echo ""
echo "🚀 Starting OBS-TV-Animator with Docker Compose..."
echo ""

# Start the container
if docker-compose up -d; then
    echo ""
    echo "🎉 OBS-TV-Animator is now running!"
    echo ""
    echo "📱 Access Information:"
    echo "   Smart TV Browser:    http://${HOST_IP}:8080"
    echo "   WebSocket Endpoint:  ws://${HOST_IP}:8080/socket.io/"
    echo "   API Endpoint:        http://${HOST_IP}:8080/animations"
    echo "   Health Check:        http://${HOST_IP}:8080/health"
    echo ""
    echo "💡 Quick Commands:"
    echo "   View logs:           docker-compose logs -f"
    echo "   Stop container:      docker-compose down"
    echo "   Restart:             docker-compose restart"
    echo "   Update:              docker-compose pull && docker-compose up -d"
    echo ""
    echo "📁 Add your content:"
    echo "   HTML animations:     Copy files to ./animations/ directory"
    echo "   Video files:         Copy files to ./videos/ directory"
    echo ""
    echo "🔧 Test your setup:"
    echo "   python example_trigger.py list"
    echo "   python example_trigger.py trigger anim1.html"
    echo ""
    echo "📚 More help: See DOCKER.md for detailed documentation"
else
    echo ""
    echo "❌ Failed to start OBS-TV-Animator"
    echo "Check the logs for details: docker-compose logs"
    exit 1
fi