# OBS-TV-Animator
A lightweight Flask-SocketIO server to display HTML/CSS/JS animations on a Smart TV, with real-time updates triggered via OBS WebSocket, StreamerBot, or REST API. Drop in new animations, trigger them remotely through WebSocket events, and create interactive displays for live streams, dashboards, or creative projects.

## Features

- 🎨 Serve HTML/CSS/JS animations to Smart TV browsers  
- 🎬 **NEW**: Support for video files (MP4, WebM, etc.) with auto-fullscreen and auto-play
- 🔄 Real-time media switching via WebSocket and REST API
- 📁 Simple folder-based media management (animations/ and videos/)
- 🎯 Built for OBS WebSocket and StreamerBot integration
- 🚀 Lightweight Flask-SocketIO server running on port 8080
- ⚡ WebSocket support for instant media updates
- 🎮 StreamerBot event handling for advanced automation
- 🎛️ Video playback controls via WebSocket (play/pause/seek/volume)

## Installation

### 🐳 Docker Installation (Recommended)

#### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Docker Desktop](https://docs.docker.com/get-started/get-docker/)

#### Accessing Your Media
- **Smart TV**: Browse to `http://[DOCKER_HOST_IP]:8080`
- **WebSocket**: Connect to `ws://[DOCKER_HOST_IP]:8080/socket.io/`
- **Add Content**: Use the front end UI at `http://[DOCKER_HOST_IP]:8080/admin` to add or remove files.

### API Endpoints

#### GET `/` - View Current Animation
Opens the currently active animation in the browser. Point your Smart TV browser to this URL.

```bash
curl http://localhost:8080/
```

#### POST `/trigger` - Switch Media
Update the current media (animation or video) by sending a JSON payload with the filename.

```bash
# Switch to HTML animation
curl -X POST http://localhost:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "anim2.html"}'

# Switch to video file  
curl -X POST http://localhost:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "my_video.mp4"}'
```

**Response:**
```json
{
  "success": true,
  "current_animation": "anim2.html",
  "message": "Animation updated to 'anim2.html'"
}
```

#### GET `/animations` - List Available Media
Get a list of all media files in the `animations/` and `videos/` directories.

```bash
curl http://localhost:8080/animations
```

**Response:**
```json
{
  "animations": ["anim1.html", "anim2.html", "anim3.html"],
  "videos": ["video1.mp4", "celebration.webm"],
  "all_media": ["anim1.html", "anim2.html", "anim3.html", "celebration.webm", "video1.mp4"],
  "current_animation": "anim1.html",
  "current_media": "anim1.html",
  "count": 5,
  "animation_count": 3,
  "video_count": 2
}
```

#### GET `/health` - Health Check
Check if the server is running properly.

```bash
curl http://localhost:8080/health
```

## Adding Media Files

### HTML Animations
1. Create an HTML file with your animation (HTML, CSS, JavaScript)
2. Make sure to use inline CSS and JS in the HTML.
3. Save it in the `animations/` directory
4. Trigger it via the `/trigger` endpoint or WebSocket events
5. Use the provided HTML templates as a scaffold for your custom animations.

### Video Files
1. Add video files to the `videos/` directory
2. Supported formats: MP4, WebM, OGG, AVI, MOV, MKV
3. Videos will auto-play, auto-fullscreen, and loop on the TV or device.
4. Use MP4 with H.264 codec for best Smart TV compatibility.


## OBS & StreamerBot Integration

This server is designed to run animations on a Smart TV while receiving WebSocket commands from OBS or StreamerBot for scene changes and events. The TV displays the animations while OBS and StreamerBot trigger changes remotely.

### Method 1: OBS WebSocket Plugin
Use the OBS WebSocket plugin to send scene change events:

```javascript
// Example OBS WebSocket script
const WebSocket = require('ws');
const ws = new WebSocket('ws://YOUR_SERVER_IP:8080/socket.io/');

// Trigger animation on scene change
ws.send(JSON.stringify({
  event: 'scene_change',
  data: {
    scene_name: 'Gaming'
  }
}));
```

### Method 2: StreamerBot Integration
Configure StreamerBot to send WebSocket events for advanced automation:

```javascript
// StreamerBot WebSocket event
{
  "event_type": "trigger_animation",
  "data": {
    "animation": "anim2.html"
  }
}
```

### Method 3: REST API (Legacy Support)
Still supports HTTP REST API calls for backwards compatibility:

```bash
# When switching to a specific scene
curl -X POST http://YOUR_SERVER_IP:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "anim2.html"}'
```

## WebSocket Events API

Connect to `ws://YOUR_SERVER_IP:8080/socket.io/` to send real-time events:

### Available Events

#### `trigger_animation`
Change the current media (animation or video) instantly:
```json
{
  "animation": "anim2.html"
}
```
```json
{
  "animation": "my_video.mp4"
}
```

#### `scene_change` 
Trigger animations based on OBS scene names:
```json
{
  "scene_name": "Gaming",
  "animation_mapping": {
    "gaming": "anim1.html",
    "chatting": "anim2.html",
    "brb": "anim3.html"
  }
}
```

#### `streamerbot_event`
Handle StreamerBot events with automatic mapping:
```json
{
  "event_type": "scene_change",
  "data": {
    "scene_name": "Gaming"
  }
}
```

#### `video_control`
Control video playback (only works when current media is a video):
```json
{
  "action": "play"
}
```
```json
{
  "action": "pause"
}
```
```json
{
  "action": "seek",
  "value": 30
}
```
```json
{
  "action": "volume", 
  "value": 0.8
}
```

#### `get_status`
Request current server status (no data required).

### Server Responses

- `animation_changed`: Broadcast when animation changes
- `status`: Current server state
- `error`: Error messages
- `info`: Informational messages

## Smart TV Setup

### 🐳 Docker Deployment
1. Find your Docker host IP address (e.g., `192.168.1.100`)
2. Start the container: `docker-compose up -d`
3. On your Smart TV, open the web browser
4. Navigate to: `http://192.168.1.100:8080`
5. The current media will display full-screen
6. Content changes automatically when triggered via WebSocket, API, or the 'admin' page.

## Tips

- **Auto-refresh:** Add a refresh timer to your animations using JavaScript
- **Responsive Design:** Use viewport units (vw, vh) for TV-friendly sizing
- **Performance:** Keep animations lightweight for Smart TV browsers
- **Testing:** Use your desktop browser to preview before deploying to TV

## License

See LICENSE file for details.