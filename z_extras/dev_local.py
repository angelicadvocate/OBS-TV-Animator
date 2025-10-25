#!/usr/bin/env python3
"""
Local Development Server for OBS-TV-Animator
Runs Flask directly on the host for maximum development speed with hot reload.

This bypasses Docker for development to provide instant file change detection.
Use this when actively developing frontend components (HTML, CSS, JS).

Requirements:
- Python 3.11+
- pip install -r requirements.txt

Usage:
- All platforms: python z_extras/dev_local.py
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path (parent directory of z_extras)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root directory so Flask can find templates, static files, etc.
os.chdir(project_root)

# Set development environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

# Import the Flask app
from app import app, socketio

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 OBS-TV-Animator LOCAL Development Server")
    print("=" * 60)
    print("")
    print("✨ Features:")
    print("  • Hot reload for Python, HTML, CSS, JS changes")
    print("  • Debug mode enabled")
    print("  • No Docker rebuild required")
    print("  • Instant feedback loop")
    print("")
    print("🌐 Access URLs:")
    print("  • TV Display:     http://localhost:5000")
    print("  • Admin Panel:    http://localhost:5000/admin")
    print("  • API Endpoint:   http://localhost:5000/api/*")
    print("")
    print("⚡ Development Tips:")
    print("  • Make changes to templates, static files, or app.py")
    print("  • Refresh browser to see changes instantly")
    print("  • Check terminal for error messages")
    print("  • Press Ctrl+C to stop server")
    print("")
    print("=" * 60)
    
    try:
        # Run Flask with SocketIO in debug mode
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n👋 Development server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting development server: {e}")
        sys.exit(1)