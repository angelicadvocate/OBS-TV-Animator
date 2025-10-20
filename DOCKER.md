# Docker Deployment Guide

This guide covers deploying OBS-TV-Animator using Docker for easy setup, updates, and management.

## Prerequisites

- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: [Install Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/angelicadvocate/OBS-TV-Animator.git
cd OBS-TV-Animator
```

### 2. Start with Docker Compose
```bash
# Start the container in the background
docker-compose up -d

# View logs
docker-compose logs -f obs-tv-animator
```

### 3. Access Your Server
- **Smart TV**: `http://[YOUR_IP]:8080`
- **WebSocket**: `ws://[YOUR_IP]:8080/socket.io/`
- **API**: `http://[YOUR_IP]:8080/animations`

## Directory Structure

```
OBS-TV-Animator/
├── animations/          # HTML animation files (mounted to container)
├── videos/             # Video files (mounted to container) 
├── data/               # Persistent state (mounted to container)
├── logs/               # Application logs (mounted to container)
├── Dockerfile          # Container build instructions
├── docker-compose.yml  # Container orchestration
├── .dockerignore      # Build context exclusions
├── docker-entrypoint.sh # Container startup script
└── .env.example       # Environment configuration template
```

## Container Management

### Starting and Stopping
```bash
# Start in background
docker-compose up -d

# Start with logs visible
docker-compose up

# Stop containers
docker-compose down

# Restart containers
docker-compose restart

# Stop and remove containers + networks
docker-compose down --volumes
```

### Viewing Logs
```bash
# All logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Logs for specific service
docker-compose logs obs-tv-animator

# Last 50 lines
docker-compose logs --tail=50
```

### Container Status
```bash
# View running containers
docker-compose ps

# View container details
docker inspect obs-tv-animator

# Execute commands inside container
docker-compose exec obs-tv-animator bash
```

## Adding Content

### HTML Animations
```bash
# Add files to animations directory
cp my_animation.html ./animations/

# Container automatically detects new files
# Trigger via API or WebSocket
curl -X POST http://localhost:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "my_animation.html"}'
```

### Video Files  
```bash
# Add video files to videos directory
cp my_video.mp4 ./videos/

# Trigger video playback
curl -X POST http://localhost:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "my_video.mp4"}'
```

## Updates and Maintenance

### Updating the Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart container
docker-compose up -d --build

# Or rebuild without cache
docker-compose build --no-cache
docker-compose up -d
```

### Container Health
```bash
# Check container health
docker-compose ps

# View health check logs
docker inspect obs-tv-animator | grep -A 20 "Health"

# Manual health check
curl -f http://localhost:8080/health
```

### Backup and Restore
```bash
# Backup persistent data
tar -czf obs-backup-$(date +%Y%m%d).tar.gz data/ animations/ videos/

# Restore from backup
tar -xzf obs-backup-20241020.tar.gz
```

## Environment Configuration

### Custom Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env

# Restart to apply changes
docker-compose up -d
```

### Environment Variables
```bash
# Application settings
FLASK_ENV=production          # production or development
PORT=8080                     # Server port
PYTHONUNBUFFERED=1           # Python output buffering

# Container settings
CONTAINER_NAME=obs-tv-animator
RESTART_POLICY=unless-stopped

# Volume paths
ANIMATIONS_PATH=./animations
VIDEOS_PATH=./videos
DATA_PATH=./data
LOGS_PATH=./logs
```

## Production Deployment

### Basic Production Setup
```bash
# Ensure data persistence
mkdir -p data logs

# Start with production settings
docker-compose up -d

# Enable automatic startup
docker update --restart unless-stopped obs-tv-animator
```

### Advanced Production (with Nginx)
```bash
# Uncomment nginx section in docker-compose.yml
# Add SSL certificates to ./ssl/ directory
# Configure nginx.conf for your domain

# Start with reverse proxy
docker-compose up -d
```

### Production Security
```bash
# Run security scan
docker scout cves obs-tv-animator

# Update base images regularly
docker-compose pull
docker-compose up -d

# Monitor logs for suspicious activity
docker-compose logs -f | grep -i error
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using port 8080
netstat -tulpn | grep 8080
# or
lsof -i :8080

# Kill process or change port in docker-compose.yml
```

#### Container Won't Start
```bash
# Check logs for errors
docker-compose logs obs-tv-animator

# Check container status
docker-compose ps

# Rebuild container
docker-compose up -d --build
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER ./animations ./videos ./data

# Or run container with current user
docker-compose exec --user $(id -u):$(id -g) obs-tv-animator bash
```

#### Network Issues
```bash
# Check Docker networks
docker network ls

# Inspect network configuration
docker network inspect obs-tv-animator_obs-network

# Test connectivity
docker-compose exec obs-tv-animator ping host.docker.internal
```

### Debug Mode
```bash
# Run in development mode
docker run -it -p 8080:8080 \
  -v $(pwd):/app \
  -e FLASK_ENV=development \
  -e FLASK_DEBUG=1 \
  obs-tv-animator

# Or edit docker-compose.yml:
# environment:
#   - FLASK_ENV=development
#   - FLASK_DEBUG=1
```

## Performance Optimization

### Resource Limits
```yaml
# Add to docker-compose.yml service section
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

### Volume Performance
```bash
# For better performance on macOS/Windows
# Use named volumes instead of bind mounts
volumes:
  - obs-data:/app/data
  - obs-animations:/app/animations
```

### Monitoring
```bash
# Monitor resource usage
docker stats obs-tv-animator

# Monitor with docker-compose
docker-compose top
```

## Integration Examples

### OBS WebSocket Connection
```javascript
// Connect OBS to Docker container
const socket = io('ws://DOCKER_HOST_IP:8080');

socket.emit('trigger_animation', {
  animation: 'scene_gaming.mp4'
});
```

### StreamerBot Configuration
```json
{
  "WebSocket_URL": "ws://DOCKER_HOST_IP:8080/socket.io/",
  "Events": {
    "NewFollower": {
      "action": "trigger_animation",
      "data": {"animation": "follower_alert.mp4"}
    }
  }
}
```

### Automation Scripts
```bash
#!/bin/bash
# Auto-update script
cd /path/to/OBS-TV-Animator
git pull
docker-compose up -d --build
echo "OBS-TV-Animator updated successfully"
```