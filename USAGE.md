# OBS-TV-Animator Usage Guide

## Quick Start

### 1. Start the Server

```bash
python app.py
```

The server will start on `http://0.0.0.0:8080` and display available animations.

### 2. Access from Smart TV

1. Find your server's IP address (e.g., `192.168.1.100`)
2. Open the Smart TV web browser
3. Navigate to: `http://192.168.1.100:8080`
4. The current animation will display

### 3. Switch Animations

#### Using curl:
```bash
curl -X POST http://192.168.1.100:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "anim2.html"}'
```

#### Using Python script:
```bash
python example_trigger.py trigger anim2.html
```

#### Using OBS:
- Use Advanced Scene Switcher plugin
- Configure webhook action to call the `/trigger` endpoint
- Set trigger conditions (e.g., scene change, hotkey)

## API Reference

### GET `/`
Returns the current animation HTML file.

**Response:** HTML content of the current animation

---

### POST `/trigger`
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

### Scene-Based Triggers

Use OBS Advanced Scene Switcher to trigger animations based on scene changes:

**Scene "Gaming":**
```bash
curl -X POST http://localhost:8080/trigger -H "Content-Type: application/json" -d '{"animation": "anim1.html"}'
```

**Scene "Chatting":**
```bash
curl -X POST http://localhost:8080/trigger -H "Content-Type: application/json" -d '{"animation": "anim2.html"}'
```

**Scene "BRB":**
```bash
curl -X POST http://localhost:8080/trigger -H "Content-Type: application/json" -d '{"animation": "anim3.html"}'
```

### Hotkey Triggers

Bind animations to OBS hotkeys for manual control during streams.

### Timer-Based Triggers

Set up automatic animation rotation every N minutes.

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
