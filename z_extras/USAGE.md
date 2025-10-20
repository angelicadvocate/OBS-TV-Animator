# OBS-TV-Animator Usage Guide

## Architecture Overview

This system consists of:
- **Smart TV**: Displays media (HTML animations or video files) by browsing to the server
- **OBS-TV-Animator Server**: Serves media to TV and accepts WebSocket/API commands
- **OBS/StreamerBot**: Sends WebSocket events to trigger media changes and video controls

## Quick Start

### 1. Start the Server

```bash
python app.py
```

The server will start on `http://0.0.0.0:8080` with WebSocket support at `ws://0.0.0.0:8080/socket.io/`.

### 2. Access from Smart TV

1. Find your server's IP address (e.g., `192.168.1.100`)
2. Open the Smart TV web browser
3. Navigate to: `http://192.168.1.100:8080`
4. The current media (animation or video) will display and auto-update when changed

### 3. Switch Media

#### Using WebSocket (Recommended):
```javascript
// Connect to WebSocket
const io = require('socket.io-client');
const socket = io('http://192.168.1.100:8080');

// Trigger animation change
socket.emit('trigger_animation', {
  animation: 'anim2.html'
});

// Trigger video change
socket.emit('trigger_animation', {
  animation: 'my_video.mp4'
});
```

#### Using REST API (Legacy):
```bash
# Switch to HTML animation
curl -X POST http://192.168.1.100:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "anim2.html"}'

# Switch to video file
curl -X POST http://192.168.1.100:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "video1.mp4"}'
```

#### Using Python script:
```bash
# HTML animations
python example_trigger.py trigger anim2.html
python example_trigger.py websocket anim2.html

# Video files
python example_trigger.py trigger video1.mp4
python example_trigger.py websocket celebration.mp4
```

#### Using OBS WebSocket Plugin:
- Install OBS WebSocket plugin
- Configure to send scene change events to server
- Animations change automatically based on scene names

#### Using StreamerBot:
- Configure WebSocket connection to server
- Set up event triggers for animations and videos
- Advanced automation and custom event handling

### 4. Video Playback Controls

When a video is currently playing, you can control it via WebSocket:

#### Using WebSocket:
```javascript
// Play/pause toggle
socket.emit('video_control', {action: 'toggle'});

// Explicit play/pause
socket.emit('video_control', {action: 'play'});
socket.emit('video_control', {action: 'pause'});

// Seek to specific time (in seconds)
socket.emit('video_control', {action: 'seek', value: 30});

// Set volume (0.0 to 1.0)
socket.emit('video_control', {action: 'volume', value: 0.8});

// Mute/unmute
socket.emit('video_control', {action: 'mute', value: true});

// Restart video from beginning
socket.emit('video_control', {action: 'restart'});
```

#### Using Python script:
```bash
# Video controls
python example_trigger.py video play
python example_trigger.py video pause
python example_trigger.py video toggle
python example_trigger.py video seek 30
python example_trigger.py video volume 0.8
python example_trigger.py video mute true
python example_trigger.py video restart
```

#### Smart TV Keyboard Controls:
- **Space/K** - Play/Pause
- **F** - Toggle fullscreen
- **M** - Mute/Unmute  
- **R** - Restart video
- **←/→** - Seek backward/forward 10 seconds

## API Reference

### WebSocket Events (Recommended)

Connect to `ws://YOUR_SERVER_IP:8080/socket.io/` and use these events:

#### Client → Server Events

**`trigger_animation`** - Change current animation
```json
{
  "animation": "anim2.html"
}
```

**`scene_change`** - OBS scene-based animation change
```json
{
  "scene_name": "Gaming",
  "animation_mapping": {
    "gaming": "anim1.html",
    "chatting": "anim2.html"
  }
}
```

**`streamerbot_event`** - StreamerBot event handling
```json
{
  "event_type": "trigger_animation",
  "data": {
    "animation": "anim3.html"
  }
}
```

**`get_status`** - Request current status (no data required)

#### Server → Client Events

**`animation_changed`** - Broadcast when animation changes
```json
{
  "previous_animation": "anim1.html",
  "current_animation": "anim2.html",
  "message": "Animation changed to 'anim2.html'"
}
```

**`status`** - Current server status
**`error`** - Error messages
**`info`** - Informational messages

---

### REST API (Legacy Support)

#### GET `/`
Returns the current animation HTML file.

**Response:** HTML content of the current animation

---

#### POST `/trigger`
Update the current animation.

**Request Body:**
```json
{
  "animation": "anim2.html"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "current_animation": "anim2.html",
  "message": "Animation updated to 'anim2.html'"
}
```

**Error Response (404):**
```json
{
  "error": "Animation 'nonexistent.html' not found",
  "available_animations": ["anim1.html", "anim2.html", "anim3.html"]
}
```

---

### GET `/animations`
List all available animations.

**Response (200):**
```json
{
  "animations": ["anim1.html", "anim2.html", "anim3.html"],
  "current_animation": "anim1.html",
  "count": 3
}
```

---

### GET `/health`
Check server health status.

**Response (200):**
```json
{
  "status": "healthy",
  "animations_available": 3
}
```

## Creating Custom Animations

### Animation Template

Create a new HTML file in the `animations/` directory:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Animation</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #000;
            overflow: hidden;
        }
        /* Your CSS animations here */
        .element {
            animation: myAnimation 2s infinite;
        }
        @keyframes myAnimation {
            0% { transform: translateX(0); }
            100% { transform: translateX(100px); }
        }
    </style>
</head>
<body>
    <div class="element">Animated Content</div>
    
    <script>
        // Optional: Auto-refresh to check for new animations
        setTimeout(() => window.location.reload(), 30000);
    </script>
</body>
</html>
```

### Best Practices

1. **Responsive Design:** Use `vw`, `vh` units for TV-friendly sizing
2. **Performance:** Keep animations lightweight for Smart TV browsers
3. **Auto-refresh:** Add refresh timer to check for animation updates
4. **Full-screen:** Design for 1920x1080 or 4K resolutions
5. **Testing:** Test in desktop browser before deploying to TV

## OBS Integration Examples

### WebSocket Scene-Based Triggers

Use OBS WebSocket plugin to send scene change events:

```javascript
// OBS WebSocket script example
const WebSocket = require('ws');
const ws = new WebSocket('ws://192.168.1.100:8080/socket.io/');

ws.on('open', function() {
    console.log('Connected to OBS-TV-Animator');
});

// Send scene change event
function changeScene(sceneName) {
    ws.send(JSON.stringify({
        event: 'scene_change',
        data: {
            scene_name: sceneName
        }
    }));
}

// Usage examples:
changeScene('Gaming');    // Will trigger anim1.html
changeScene('Chatting');  // Will trigger anim2.html
changeScene('BRB');       // Will trigger anim3.html
```

### OBS Advanced Scene Switcher

Configure Advanced Scene Switcher to send WebSocket messages:

1. Add WebSocket action
2. Set URL: `ws://YOUR_IP:8080/socket.io/`
3. Configure message format:
```json
{
  "event": "trigger_animation",
  "data": {
    "animation": "anim1.html"
  }
}
```

### Manual Hotkey Triggers

Bind WebSocket commands to OBS hotkeys for instant control.

### Timer-Based Triggers

Set up automatic animation rotation using WebSocket events.

## StreamerBot Integration

### WebSocket Connection Setup

1. In StreamerBot, create a new WebSocket client
2. Set URL: `ws://YOUR_SERVER_IP:8080/socket.io/`
3. Configure connection settings for automatic reconnection

### Event Actions

Configure StreamerBot actions to send WebSocket events:

#### Scene Change Action
```json
{
  "event_type": "scene_change",
  "data": {
    "scene_name": "%sceneName%"
  }
}
```

#### Custom Animation Trigger
```json
{
  "event_type": "trigger_animation", 
  "data": {
    "animation": "anim2.html"
  }
}
```

#### Follow/Donation Event Animation  
```json
{
  "event_type": "custom_animation",
  "data": {
    "animation": "celebration.html"
  }
}
```

#### Video Event Triggers
```json
{
  "event_type": "trigger_animation",
  "data": {
    "animation": "celebration.mp4"
  }
}
```

### StreamerBot Action Examples

**Follower Alert (Video):**
- Trigger: New Follower
- Action Type: WebSocket Send
- Message: 
```json
{
  "event_type": "trigger_animation",
  "data": {
    "animation": "follower_alert.mp4"
  }
}
```

**Donation Alert (Animation):**
- Trigger: Donation Received
- Action Type: WebSocket Send
- Message: 
```json
{
  "event_type": "trigger_animation",
  "data": {
    "animation": "donation_alert.html"
  }
}
```

**Scene-Specific Backgrounds (Mixed Media):**
- Trigger: OBS Scene Change
- Action Type: WebSocket Send  
- Message:
```json
{
  "event_type": "scene_change",
  "data": {
    "scene_name": "%sceneName%",
    "animation_mapping": {
      "gaming": "gaming_bg.mp4",
      "chatting": "chat_bg.html", 
      "brb": "brb_video.mp4",
      "starting": "countdown.html"
    }
  }
}
```

**Timed Rotation:**
- Trigger: Timed Action (every 5 minutes)
- Action Type: WebSocket Send
- Cycles through different ambient animations

## Troubleshooting

### Server not starting
- Check if port 8080 is already in use
- Verify Python and Flask are installed: `pip install -r requirements.txt`

### Smart TV can't connect
- Verify both devices are on the same network
- Check firewall settings allow port 8080
- Try accessing from desktop browser first: `http://localhost:8080`

### Animation not updating
- Check the animation file exists in `animations/` directory
- Verify the filename in the trigger request matches exactly
- Check server logs for error messages

### Animation not displaying correctly
- Test in desktop browser first
- Check browser console for JavaScript errors
- Verify CSS animations are supported by TV browser

## Advanced Usage

### Running as a Service

Create a systemd service file (Linux):

```ini
[Unit]
Description=OBS-TV-Animator Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/OBS-TV-Animator
ExecStart=/usr/bin/python3 /path/to/OBS-TV-Animator/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Production Deployment

For production use, consider using a production WSGI server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### Remote Access

For remote access outside your local network:
1. Set up port forwarding on your router (port 8080)
2. Use a reverse proxy (nginx, Apache)
3. Consider adding authentication for security
