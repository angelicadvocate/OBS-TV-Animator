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
        # Only initialize automation in the main process, not in reloader child process
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            # Import automation components inside main block to avoid double initialization
            from app import DATA_DIR, TriggerFileWatcher, OBSSceneWatcher, OBSWebSocketClient
            import app as app_module
            
            # Initialize automation features for development
            print("\n🔧 Initializing automation features...")
            
            # Initialize file trigger watcher for StreamerBot
            print("🔍 Starting file trigger watcher...")
            trigger_file = DATA_DIR / "trigger.txt"
            file_watcher = TriggerFileWatcher(str(trigger_file))
            file_watcher.start_watching()
            print("✓ File trigger watcher started")
            
            # Initialize OBS Scene Watcher for automatic animation triggering
            print("🎬 Starting OBS Scene Watcher...")
            obs_scene_file = DATA_DIR / "config" / "obs_current_scene.json"
            obs_mappings_file = DATA_DIR / "config" / "obs_mappings.json"
            app_module.obs_scene_watcher = OBSSceneWatcher(str(obs_scene_file), str(obs_mappings_file))
            app_module.obs_scene_watcher.start_watching()
            print("✓ OBS Scene Watcher started")
            
            # Initialize OBS WebSocket client for development
            print("🎬 Initializing OBS WebSocket client...")
            app_module.obs_client = OBSWebSocketClient()
            print("✓ OBS WebSocket client initialized")
            
            # Attempt auto-connection if settings exist
            print("📋 Checking for existing OBS settings...")
            if app_module.obs_client.load_settings():
                print("📋 Found OBS settings, enabling persistent connection...")
                try:
                    app_module.obs_client.auto_reconnect_enabled = True
                    app_module.obs_client.should_be_connected = True
                    app_module.obs_client.enable_persistent_connection()
                    
                    if app_module.obs_client.connected:
                        print("✅ SUCCESSFULLY CONNECTED TO OBS - PERSISTENT CONNECTION ACTIVE")
                    else:
                        print("⚠️  Initial connection failed but PERSISTENT RECONNECTION IS ACTIVE")
                        
                except Exception as e:
                    print(f"❌ OBS connection error during development startup: {e}")
                    try:
                        app_module.obs_client.auto_reconnect_enabled = True
                        app_module.obs_client.should_be_connected = True
                        app_module.obs_client._start_connection_monitor()
                        print("✅ FORCED connection monitor started - will reconnect when OBS available")
                    except Exception as monitor_error:
                        print(f"❌ Could not start connection monitor: {monitor_error}")
            else:
                print("ℹ️  No OBS settings found - connection will be available when configured")
            
            print("✅ Automation features initialized!\n")
        
        # Run Flask with SocketIO in debug mode
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,  # Re-enabled with proper reloader detection
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n👋 Development server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting development server: {e}")
        sys.exit(1)