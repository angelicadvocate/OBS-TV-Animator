# OBS-TV-Animator
A lightweight Flask-based server to display HTML/CSS/JS animations on a Smart TV, with dynamic updates triggered via OBS or webhooks. Drop in new animations, trigger them remotely, and create interactive or looping displays for live streams, dashboards, or creative projects.

## Features

- 🎨 Serve HTML/CSS/JS animations to Smart TV browsers
- 🔄 Dynamic animation switching via REST API
- 📁 Simple folder-based animation management
- 🎯 Built specifically for OBS integration
- 🚀 Lightweight Flask server running on port 8080

## Installation

```bash
# Clone the repository
git clone https://github.com/angelicadvocate/OBS-TV-Animator.git
cd OBS-TV-Animator

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://0.0.0.0:8080` and be accessible from any device on your network.

### API Endpoints

#### GET `/` - View Current Animation
Opens the currently active animation in the browser. Point your Smart TV browser to this URL.

```bash
curl http://localhost:8080/
```

#### POST `/trigger` - Switch Animation
Update the current animation by sending a JSON payload with the animation filename.

```bash
curl -X POST http://localhost:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "anim2.html"}'
```

**Response:**
```json
{
  "success": true,
  "current_animation": "anim2.html",
  "message": "Animation updated to 'anim2.html'"
}
```

#### GET `/animations` - List Available Animations
Get a list of all animation files in the `animations/` directory.

```bash
curl http://localhost:8080/animations
```

**Response:**
```json
{
  "animations": ["anim1.html", "anim2.html", "anim3.html"],
  "current_animation": "anim1.html",
  "count": 3
}
```

#### GET `/health` - Health Check
Check if the server is running properly.

```bash
curl http://localhost:8080/health
```

## Project Structure

```
OBS-TV-Animator/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── animations/           # Animation HTML files
│   ├── anim1.html       # Sample: Bouncing ball
│   ├── anim2.html       # Sample: Rotating squares
│   └── anim3.html       # Sample: Pulsing circles
├── templates/            # Flask templates (currently unused)
├── static/              # Static assets (CSS, JS, images)
├── data/                # Application data
│   └── state.json      # Tracks current animation state
└── README.md
```

## Creating Custom Animations

1. Create an HTML file with your animation (HTML, CSS, JavaScript)
2. Save it in the `animations/` directory
3. Trigger it via the `/trigger` endpoint or let users manually select it

### Example Animation Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Custom Animation</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #000;
            overflow: hidden;
        }
        /* Your custom styles here */
    </style>
</head>
<body>
    <!-- Your animation content here -->
    <script>
        // Optional: Auto-refresh every 30 seconds to check for updates
        setTimeout(() => window.location.reload(), 30000);
    </script>
</body>
</html>
```

## OBS Integration

### Method 1: Browser Source
1. In OBS, add a **Browser Source**
2. Set URL to: `http://YOUR_SERVER_IP:8080/`
3. Set width and height to match your canvas
4. The animation will display in your stream

### Method 2: Webhook Trigger
Use OBS Advanced Scene Switcher or custom scripts to trigger animations:

```bash
# When switching to a specific scene
curl -X POST http://YOUR_SERVER_IP:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "anim2.html"}'
```

## Smart TV Setup

1. Find your computer's local IP address (e.g., `192.168.1.100`)
2. Start the server: `python app.py`
3. On your Smart TV, open the web browser
4. Navigate to: `http://192.168.1.100:8080`
5. The current animation will display full-screen

## Tips

- **Auto-refresh:** Add a refresh timer to your animations using JavaScript
- **Responsive Design:** Use viewport units (vw, vh) for TV-friendly sizing
- **Performance:** Keep animations lightweight for Smart TV browsers
- **Testing:** Use your desktop browser to preview before deploying to TV

## License

See LICENSE file for details.
