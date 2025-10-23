#!/bin/bash
echo "===================================="
echo "OBS-TV-Animator Development Server"
echo "===================================="
echo ""
echo "Starting development server with hot reload..."
echo "Changes to Python, HTML, CSS, and JS files will be reflected immediately!"
echo ""
echo "Press Ctrl+C to stop the development server"
echo ""

# Stop any existing containers
docker-compose -f docker-compose.dev.yml down 2>/dev/null

# Start development server
docker-compose -f docker-compose.dev.yml up --build

echo ""
echo "Development server stopped."