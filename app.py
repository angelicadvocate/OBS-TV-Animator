#!/usr/bin/env python3
"""
OBS-TV-Animator: A Flask-SocketIO server to display HTML/CSS/JS animations on a Smart TV.
Supports dynamic updates triggered via OBS WebSocket, StreamerBot, or REST API.
"""

__version__ = "0.8.6"

import json
import os
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from threading import Thread
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import asyncio
from thumbnail_service import get_thumbnail_service
import websockets
import threading
from obswebsocket import obsws, requests, events

app = Flask(__name__)
app.config['SECRET_KEY'] = 'obs-tv-animator-secret-key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access the admin panel.'

# Configuration
MAIN_PORT = int(os.environ.get('PORT', 8080))
WEBSOCKET_PORT = MAIN_PORT + 1  # Raw WebSocket port is always main port + 1

def get_current_port():
    """Get the current server port based on environment (development vs production)"""
    # Development mode (via dev_local.py) uses Flask's default port 5000
    if os.environ.get('FLASK_ENV') == 'development':
        return 5000
    # Production mode uses the configured MAIN_PORT
    return MAIN_PORT

ANIMATIONS_DIR = Path(__file__).parent / "animations"
VIDEOS_DIR = Path(__file__).parent / "videos"
DATA_DIR = Path(__file__).parent / "data"
CONFIG_DIR = DATA_DIR / "config"  # Config now under data directory
LOGS_DIR = DATA_DIR / "logs"      # Logs now under data directory
THUMBNAILS_DIR = DATA_DIR / "thumbnails"  # Thumbnails directory
STATE_FILE = DATA_DIR / "state.json"
USERS_FILE = CONFIG_DIR / "users.json"

# Supported file extensions
HTML_EXTENSIONS = {'.html', '.htm'}
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.ogg', '.avi', '.mov', '.mkv'}

# Connected devices tracking
connected_devices = {}  # {session_id: {'type': 'tv'|'admin', 'user_agent': str, 'connected_at': timestamp}}
admin_sessions = set()  # Track admin dashboard sessions

# OBS WebSocket client and scene watcher
obs_client = None
obs_scene_watcher = None

# Authentication classes and functions
class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username

@login_manager.user_loader
def load_user(username):
    """Load user for Flask-Login"""
    users_data = load_users_config()
    if username in users_data.get('admin_users', {}):
        return User(username)
    return None

def load_users_config():
    """Load users configuration from file"""
    try:
        if USERS_FILE.exists():
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading users config: {e}")
    
    # Default config if file doesn't exist
    return {
        "admin_users": {
            "admin": {
                "password": "admin123",
                "created_at": datetime.now().isoformat(),
                "permissions": ["read", "write", "delete", "upload"]
            }
        }
    }

def verify_password(username, password):
    """Verify user password"""
    users_data = load_users_config()
    admin_users = users_data.get('admin_users', {})
    
    if username in admin_users:
        stored_password = admin_users[username]['password']
        # In production, you'd want to hash passwords
        return stored_password == password
    
    return False

def admin_required(f):
    """Decorator to require admin authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def api_admin_required(f):
    """Decorator to require admin authentication for API routes - returns JSON errors"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required', 'authenticated': False}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_connected_devices_info():
    """Get information about connected devices"""
    tv_devices = []
    admin_count = 0
    streamerbot_devices = []
    
    # Get Socket.IO devices (admin dashboard and TV displays)
    for session_id, device_info in connected_devices.items():
        if device_info['type'] == 'tv':
            tv_devices.append({
                'id': session_id,
                'type': 'tv',
                'user_agent': device_info['user_agent'],
                'connected_at': device_info['connected_at']
            })
        elif device_info['type'] == 'admin':
            admin_count += 1
    
    # Get StreamerBot raw WebSocket connections
    if raw_websocket_server and raw_websocket_server.clients:
        for client in raw_websocket_server.clients:
            try:
                streamerbot_devices.append({
                    'id': f"streamerbot_{client.remote_address[0]}:{client.remote_address[1]}",
                    'type': 'streamerbot',
                    'remote_address': client.remote_address,
                    'connected': True
                })
            except Exception as e:
                # Handle case where client connection info is not available
                print(f"Error getting StreamerBot client info: {e}")
    
    streamerbot_count = len(streamerbot_devices)
    
    return {
        'tv_devices': tv_devices,
        'tv_count': len(tv_devices),
        'admin_count': admin_count,
        'streamerbot_devices': streamerbot_devices,
        'streamerbot_count': streamerbot_count,
        'total_count': len(connected_devices) + streamerbot_count
    }


def get_tv_devices_count():
    """Get count of connected TV devices (excluding admin)"""
    return len([d for d in connected_devices.values() if d['type'] == 'tv'])


class TriggerFileWatcher:
    """Watch for file-based triggers from StreamerBot"""
    def __init__(self, trigger_file_path):
        self.trigger_file_path = trigger_file_path
        self.last_modified = 0
        self.running = True
        
    def start_watching(self):
        """Start watching the trigger file in a background thread"""
        thread = Thread(target=self._watch_file, daemon=True)
        thread.start()
        print(f"🔍 Started watching trigger file: {self.trigger_file_path}")
        
    def _watch_file(self):
        """Watch for changes to the trigger file"""
        while self.running:
            try:
                if os.path.exists(self.trigger_file_path):
                    current_modified = os.path.getmtime(self.trigger_file_path)
                    
                    if current_modified > self.last_modified:
                        self.last_modified = current_modified
                        
                        # Read the animation name from the file
                        with open(self.trigger_file_path, 'r') as f:
                            animation_name = f.read().strip()
                            
                        if animation_name:
                            print(f"📂 File trigger received: {animation_name}")
                            self._handle_trigger(animation_name)
                            
                        # Delete the file after processing
                        os.remove(self.trigger_file_path)
                        
            except Exception as e:
                print(f"Error watching trigger file: {e}")
                
            time.sleep(0.1)  # Check every 100ms for fast response
            
    def _handle_trigger(self, animation_name):
        """Handle the animation trigger"""
        try:
            # Validate that the media file exists
            media_path, media_type = find_media_file(animation_name)
            if not media_path:
                print(f"❌ Media file '{animation_name}' not found")
                return
                
            # Update state
            state = load_state()
            state['current_animation'] = animation_name
            save_state(state)

            # Emit animation change to all clients
            socketio.emit('animation_changed', {
                'current_animation': animation_name,
                'media_type': media_type,
                'message': f"Media changed to '{animation_name}' ({media_type}) via file trigger",
                'refresh_page': True
            })

            # Emit explicit page refresh
            socketio.emit('page_refresh', {
                'reason': 'file_trigger',
                'new_media': animation_name,
                'media_type': media_type
            })

            print(f"✅ Successfully triggered animation: {animation_name} ({media_type})")
            
        except Exception as e:
            print(f"❌ Error handling trigger: {e}")
            
    def stop_watching(self):
        """Stop watching the trigger file"""
        self.running = False


class OBSSceneWatcher:
    """File watcher that monitors obs_current_scene.json and triggers animations based on mappings"""
    
    def __init__(self, scene_file_path, mappings_file_path):
        self.scene_file_path = Path(scene_file_path)
        self.mappings_file_path = Path(mappings_file_path)
        self.running = False
        self.watch_thread = None
        self.last_scene = None
        self.last_modified = 0
        
        print(f"🎬 OBS Scene Watcher initialized:")
        print(f"   Scene file: {self.scene_file_path}")
        print(f"   Mappings file: {self.mappings_file_path}")
    
    def start_watching(self):
        """Start watching the OBS scene file for changes"""
        if self.running:
            print("⚠️ OBS Scene Watcher is already running")
            return
            
        self.running = True
        self.watch_thread = Thread(target=self._watch_scene_file, daemon=True)
        self.watch_thread.start()
        print("🎬 OBS Scene Watcher started successfully")
    
    def _watch_scene_file(self):
        """Watch the scene file for changes and trigger animations"""
        print("👀 OBS Scene Watcher monitoring started...")
        
        while self.running:
            try:
                if self.scene_file_path.exists():
                    # Check if file was modified
                    current_modified = self.scene_file_path.stat().st_mtime
                    
                    if current_modified > self.last_modified:
                        self.last_modified = current_modified
                        print(f"🎬 [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Scene file changed detected")
                        
                        # Read the current scene
                        try:
                            with open(self.scene_file_path, 'r', encoding='utf-8') as f:
                                scene_data = json.load(f)
                                current_scene = scene_data.get('current_scene')
                                
                            if current_scene and current_scene != self.last_scene:
                                print(f"🎬 Scene change detected: '{self.last_scene}' → '{current_scene}'")
                                self.last_scene = current_scene
                                self._handle_scene_change(current_scene)
                                
                        except (json.JSONDecodeError, KeyError, Exception) as e:
                            print(f"❌ Error reading scene file: {e}")
                
                time.sleep(0.1)  # Check every 100ms for responsiveness
                
            except Exception as e:
                print(f"❌ Scene watcher error: {e}")
                time.sleep(1)  # Wait longer on errors
    
    def _handle_scene_change(self, scene_name):
        """Handle a scene change by checking mappings and triggering animations"""
        try:
            print(f"🎭 Processing scene change: '{scene_name}'")
            
            # Load current scene mappings
            mappings = self._load_scene_mappings()
            if not mappings:
                print("ℹ️ No scene mappings configured")
                return
            
            # Find matching animation for this scene
            animation_name = None
            for mapping in mappings:
                if mapping.get('sceneName') == scene_name:
                    animation_name = mapping.get('animation')
                    break
            
            if animation_name:
                print(f"🎭 Found mapping: '{scene_name}' → '{animation_name}'")
                self._trigger_animation(animation_name, scene_name)
            else:
                print(f"ℹ️ No animation mapping found for scene '{scene_name}'")
                
        except Exception as e:
            print(f"❌ Error handling scene change: {e}")
    
    def _load_scene_mappings(self):
        """Load scene mappings from the mappings file"""
        try:
            if self.mappings_file_path.exists():
                with open(self.mappings_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle both formats: direct array or wrapped in 'mappings' key
                    if isinstance(data, list):
                        mappings = data
                    else:
                        mappings = data.get('mappings', [])
                    print(f"📋 Loaded {len(mappings)} scene mappings")
                    return mappings
            else:
                print("⚠️ Scene mappings file not found")
                return []
        except Exception as e:
            print(f"❌ Error loading scene mappings: {e}")
            return []
    
    def _trigger_animation(self, animation_name, scene_name):
        """Trigger an animation by directly updating state and emitting SocketIO commands"""
        try:
            print(f"🎬 Triggering animation '{animation_name}' for scene '{scene_name}'")
            
            # Validate that the media file exists
            media_path, media_type = find_media_file(animation_name)
            if not media_path:
                print(f"❌ Animation file '{animation_name}' not found")
                return
            
            # Update state directly (same as /trigger route)
            state = load_state()
            state['current_animation'] = animation_name
            save_state(state)
            print(f"💾 Updated backend state to: {animation_name}")
            
            # Import socketio from the global scope
            global socketio
            if socketio:
                # Emit animation change to all clients (same as /trigger route)
                socketio.emit('animation_changed', {
                    'current_animation': animation_name,
                    'media_type': media_type,
                    'message': f"Media changed to '{animation_name}' ({media_type})",
                    'refresh_page': True
                })
                print(f"📡 [AUTO-TRIGGER] Emitted 'animation_changed' for '{animation_name}' with refresh_page=True")

                # Emit explicit page refresh (same as /trigger route)
                socketio.emit('page_refresh', {
                    'reason': 'media_changed',
                    'new_media': animation_name,
                    'media_type': media_type
                })
                print(f"📡 [AUTO-TRIGGER] Emitted 'page_refresh' for '{animation_name}' - TV should reload now")
                
                print(f"✅ Successfully auto-triggered animation: {animation_name} ({media_type}) for scene: {scene_name}")
            else:
                print(f"❌ SocketIO not available for auto-trigger")
            
        except Exception as e:
            print(f"❌ Error triggering animation: {e}")
    
    def stop_watching(self):
        """Stop watching the scene file"""
        self.running = False
        if self.watch_thread and self.watch_thread.is_alive():
            print("🛑 Stopping OBS Scene Watcher...")
            self.watch_thread.join(timeout=2)
        print("🛑 OBS Scene Watcher stopped")


class OBSWebSocketClient:
    """OBS WebSocket Client to handle scene change events and animation triggers"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.settings = {}
        self.scene_mappings = []
        self.connection_thread = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 20  # Increased for better persistence
        self.auto_reconnect_enabled = True
        self.connection_monitor_thread = None
        self.should_be_connected = False  # Track intended connection state
        
    def load_settings(self):
        """Load OBS connection settings from config file"""
        try:
            obs_config_path = DATA_DIR / 'config' / 'obs_settings.json'
            print(f"📂 Looking for settings at: {obs_config_path}")
            
            if obs_config_path.exists():
                print("✅ Settings file found, loading...")
                with open(obs_config_path, 'r') as f:
                    self.settings = json.load(f)
                
                # Log settings without password
                settings_log = self.settings.copy()
                if 'password' in settings_log and settings_log['password']:
                    settings_log['password'] = '[REDACTED]'
                else:
                    settings_log['password'] = '[EMPTY]'
                print(f"📋 Loaded settings: {settings_log}")
                return True
            else:
                print("❌ Settings file not found")
                return False
        except Exception as e:
            print(f"❌ Error loading OBS settings: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_scene_mappings(self):
        """Load scene to animation mappings from config file"""
        try:
            mappings_path = DATA_DIR / 'config' / 'obs_mappings.json'
            if mappings_path.exists():
                with open(mappings_path, 'r') as f:
                    self.scene_mappings = json.load(f)
                return True
            return False
        except Exception as e:
            print(f"❌ Error loading OBS scene mappings: {e}")
            return False
    
    def connect(self):
        """Establish connection to OBS WebSocket server"""
        if not self.load_settings():
            print("⚠️  No OBS settings found, skipping connection")
            return False
            
        if not self.load_scene_mappings():
            print("⚠️  No scene mappings found, OBS events will be ignored")
            self.scene_mappings = []
        
        try:
            print(f"🔌 Attempting to connect to OBS at {self.settings.get('host', 'localhost')}:{self.settings.get('port', 4455)}")
            
            # Create OBS WebSocket client
            self.client = obsws(
                host=self.settings.get('host', 'localhost'),
                port=self.settings.get('port', 4455),
                password=self.settings.get('password', '')
            )
            
            # Connect to OBS
            self.client.connect()
            
            # Test the connection by getting version
            version_info = self.client.call(requests.GetVersion())
            print(f"✅ Connected to OBS Studio {version_info.getObsVersion()}")
            print(f"✅ OBS WebSocket version: {version_info.getObsWebSocketVersion()}")
            
            self.connected = True
            self.should_be_connected = True  # Mark that we want to stay connected
            self.reconnect_attempts = 0
            
            # Register for scene change events
            try:
                # Try newer OBS WebSocket event first
                if hasattr(events, 'CurrentProgramSceneChanged'):
                    self.client.register(self._on_scene_changed, events.CurrentProgramSceneChanged)
                    print("👂 Registered for CurrentProgramSceneChanged events")
                elif hasattr(events, 'SwitchScenes'):
                    self.client.register(self._on_scene_changed, events.SwitchScenes)
                    print("👂 Registered for SwitchScenes events (fallback)")
                else:
                    print("⚠️ No suitable scene change event found")
            except Exception as event_error:
                print(f"⚠️ Error registering for scene events: {event_error}")
                # Try fallback
                try:
                    self.client.register(self._on_scene_changed, events.SwitchScenes)
                    print("👂 Fallback: Registered for SwitchScenes events")
                except Exception as fallback_error:
                    print(f"❌ Failed to register for any scene events: {fallback_error}")
            
            print("👂 OBS event listener setup complete, waiting for scene changes...")
            
            # Start connection monitor for persistent connection
            self._start_connection_monitor()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to OBS: {e}")
            self.connected = False
            self._schedule_reconnect()
            return False
    
    def _on_scene_changed(self, message):
        """Handle OBS scene change events - BULLETPROOF VERSION"""
        scene_name = None
        event_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        try:
            print(f"🎬 [{event_time}] Scene change event received, type: {type(message)}")
            
            # Handle different event formats with bulletproof extraction
            try:
                if hasattr(message, 'sceneName') and message.sceneName:
                    scene_name = str(message.sceneName)
                    print(f"🎬 Got scene name from .sceneName: {scene_name}")
                elif hasattr(message, 'getSceneName') and callable(message.getSceneName):
                    scene_name = str(message.getSceneName())
                    print(f"🎬 Got scene name from .getSceneName(): {scene_name}")
                elif hasattr(message, 'datain') and isinstance(message.datain, dict) and 'sceneName' in message.datain:
                    scene_name = str(message.datain['sceneName'])
                    print(f"🎬 Got scene name from datain: {scene_name}")
                else:
                    print(f"🎬 Could not extract scene name. Message attributes: {dir(message)}")
                    if hasattr(message, '__dict__'):
                        print(f"🎬 Message dict: {message.__dict__}")
                    return
            except Exception as extract_error:
                print(f"❌ CRITICAL: Scene name extraction failed: {extract_error}")
                return
            
            if not scene_name or not isinstance(scene_name, str) or len(scene_name.strip()) == 0:
                print(f"❌ Invalid scene name extracted: '{scene_name}'")
                return
                
            scene_name = scene_name.strip()
            print(f"🎬 [{event_time}] INSTANT OBS Scene change detected: '{scene_name}'")
            
        except Exception as initial_error:
            print(f"❌ CRITICAL: Initial scene change processing failed: {initial_error}")
            print(f"❌ Message type: {type(message)}, Message: {message}")
            return
        
        # Process the scene change in separate try blocks to prevent cascading failures
        
        # 1. Update scene data via API route (for file storage only)
        try:
            import requests
            import json
            
            # Get the current server port dynamically
            current_port = get_current_port()
            
            # Use the existing API route to save scene data
            response = requests.post(f'http://localhost:{current_port}/api/obs/current-scene', 
                                   json={'current_scene': scene_name},
                                   headers={'Content-Type': 'application/json'},
                                   timeout=1)
            
            storage_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            if response.status_code == 200:
                print(f"💾 [{storage_time}] INSTANT scene data saved: {scene_name}")
            else:
                print(f"⚠️ Scene data save failed (status {response.status_code}): {response.text}")
        except Exception as api_error:
            print(f"⚠️ Scene data save failed (non-critical): {api_error}")
            # Don't return - continue with other operations
        
        # 2. Emit to frontend (independent operation)
        try:
            global socketio
            if 'socketio' in globals() and socketio:
                emit_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                socketio.emit('scene_changed', {
                    'scene_name': scene_name,
                    'timestamp': time.time(),
                    'event_time': emit_time
                })
                print(f"📡 [{emit_time}] INSTANT Socket.IO emission to frontend: {scene_name}")
            else:
                print("⚠️ SocketIO not available for scene change notification")
        except Exception as emit_error:
            print(f"⚠️ Socket.IO emission failed (non-critical): {emit_error}")
            # Don't return - continue with other operations
        
        # Note: Animation triggering is now handled by OBSSceneWatcher file watcher
        # This prevents duplicate triggers and provides better separation of concerns
        
        print(f"✅ [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Scene change processing completed successfully")
    
    def _schedule_reconnect(self):
        """Schedule a reconnection attempt"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            delay = min(30, 2 ** self.reconnect_attempts)  # Exponential backoff, max 30 seconds
            print(f"⏰ Scheduling OBS reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} in {delay} seconds")
            
            def reconnect_after_delay():
                time.sleep(delay)
                if not self.connected:  # Only reconnect if still disconnected
                    print(f"🔄 Attempting OBS reconnection ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
                    self.connect()
            
            Thread(target=reconnect_after_delay, daemon=True).start()
        else:
            print(f"❌ Max OBS reconnection attempts ({self.max_reconnect_attempts}) reached. Will retry later...")
            # Reset attempts after a longer delay to try again
            def reset_attempts_later():
                time.sleep(300)  # Wait 5 minutes before allowing retries again
                self.reconnect_attempts = 0
                if self.should_be_connected and not self.connected:
                    print("🔄 Retrying OBS connection after cooldown period...")
                    self._schedule_reconnect()
            Thread(target=reset_attempts_later, daemon=True).start()
    
    def _start_connection_monitor(self):
        """Start a background thread to monitor and maintain OBS connection"""
        if self.connection_monitor_thread and self.connection_monitor_thread.is_alive():
            return
            
        def connection_monitor():
            print("👀 Starting OBS connection monitor with PERSISTENT RECONNECTION...")
            monitor_loop_count = 0
            while self.auto_reconnect_enabled:
                try:
                    time.sleep(10)  # Check every 10 seconds
                    monitor_loop_count += 1
                    
                    # Debug logging every few loops
                    if monitor_loop_count % 6 == 0:  # Every minute
                        print(f"👀 Connection monitor status: should_connect={self.should_be_connected}, connected={self.connected}, auto_reconnect={self.auto_reconnect_enabled}")
                    
                    if self.should_be_connected and not self.connected:
                        print("🔄 Connection monitor: OBS DISCONNECTED - FORCING RECONNECT...")
                        success = self.connect()
                        if success:
                            print("✅ Connection monitor: RECONNECTION SUCCESSFUL")
                        else:
                            print("❌ Connection monitor: Reconnection failed, will retry in 10 seconds")
                    elif self.connected and self.client:
                        # Test connection with a simple request
                        try:
                            self.client.call(requests.GetVersion())
                            # Connection is healthy - no logging needed
                        except Exception as e:
                            print(f"🔄 Connection monitor: OBS connection test FAILED: {e}")
                            print("🔄 Marking as disconnected and forcing reconnect...")
                            self.connected = False
                            if self.should_be_connected:
                                success = self.connect()
                                if success:
                                    print("✅ Connection monitor: RECONNECTION after test failure SUCCESSFUL")
                                else:
                                    print("❌ Connection monitor: Reconnection after test failure FAILED")
                                
                except Exception as e:
                    print(f"❌ CRITICAL: Connection monitor error: {e}")
                    print("🔄 Connection monitor continuing despite error...")
                    time.sleep(30)  # Wait longer on monitor errors
                    
        self.connection_monitor_thread = Thread(target=connection_monitor, daemon=True)
        self.connection_monitor_thread.start()
    
    def disconnect(self, permanent=False, force=False):
        """Disconnect from OBS WebSocket server
        
        Args:
            permanent (bool): If True, disables auto-reconnection. If False, allows reconnection.
            force (bool): If True, bypasses settings check for permanent disconnection.
        """
        self.connected = False
        
        if permanent and not force:
            # Check if OBS is enabled in settings before allowing permanent disconnect
            try:
                obs_config_path = DATA_DIR / 'config' / 'obs_settings.json'
                if obs_config_path.exists():
                    with open(obs_config_path, 'r') as f:
                        settings = json.load(f)
                    
                    if settings.get('enabled', True):
                        print("🚨 REFUSING permanent disconnect - OBS is enabled in settings!")
                        print("🔄 Keeping auto-reconnection active per user settings")
                        # Don't disable auto-reconnection if settings say to stay connected
                        return
                        
            except Exception as settings_error:
                print(f"⚠️ Could not check settings for disconnect: {settings_error}")
                # If we can't check settings, be safe and keep connection active
                print("🚨 Refusing permanent disconnect due to settings check failure")
                return
            
            self.should_be_connected = False  # Disable auto-reconnection
            self.auto_reconnect_enabled = False
            print("🔌 Permanently disconnecting from OBS WebSocket server")
        else:
            print("🔌 Temporarily disconnecting from OBS WebSocket server")
            
        if self.client:
            try:
                self.client.disconnect()
                print("✅ Disconnected from OBS WebSocket server")
            except Exception as e:
                print(f"⚠️  Error during OBS disconnect: {e}")
            finally:
                self.client = None
    
    def test_connection(self):
        """Test OBS WebSocket connection without establishing persistent connection"""
        print("📋 test_connection() called")
        
        if not self.load_settings():
            print("❌ No settings found")
            return False, "No OBS settings configured"
        
        # Log connection attempt details (without password)
        connection_info = {
            'host': self.settings.get('host', 'localhost'),
            'port': self.settings.get('port', 4455),
            'password_set': bool(self.settings.get('password', ''))
        }
        print(f"🔌 Attempting connection to: {connection_info}")
        
        try:
            import time
            start_time = time.time()
            
            print("📱 Creating obsws client...")
            # Create temporary client for testing
            test_client = obsws(
                host=self.settings.get('host', 'localhost'),
                port=self.settings.get('port', 4455),
                password=self.settings.get('password', '')
            )
            print("✅ obsws client created successfully")
            
            # Test the connection
            print("🔗 Calling connect()...")
            test_client.connect()
            connect_time = time.time() - start_time
            print(f"✅ Connected successfully in {connect_time:.2f}s")
            
            print("📞 Calling GetVersion()...")
            version_start = time.time()
            version_info = test_client.call(requests.GetVersion())
            version_time = time.time() - version_start
            print(f"✅ GetVersion completed in {version_time:.2f}s")
            
            print("🔌 Disconnecting...")
            test_client.disconnect()
            
            total_time = time.time() - start_time
            obs_version = version_info.getObsVersion()
            success_msg = f"Connected to OBS Studio {obs_version} (total: {total_time:.2f}s)"
            print(f"🎉 {success_msg}")
            
            return True, success_msg
            
        except Exception as e:
            total_time = time.time() - start_time if 'start_time' in locals() else 0
            error_msg = f"Connection failed: {str(e)}"
            print(f"❌ {error_msg} (after {total_time:.2f}s)")
            
            # Add more specific error information
            if "10060" in str(e):
                print("🔍 Error 10060 = Connection timeout (target not responding)")
                print("💡 Possible causes:")
                print("   - OBS Studio not running")
                print("   - OBS WebSocket server not enabled")
                print("   - Wrong host/port")
                print("   - Firewall blocking connection")
            elif "10061" in str(e):
                print("🔍 Error 10061 = Connection actively refused")
                print("💡 Possible causes:")
                print("   - OBS WebSocket server disabled")
                print("   - Wrong port number")
            
            return False, error_msg
    
    def get_current_scene(self):
        """Get the current active scene from OBS"""
        if not self.connected or not self.client:
            return None
        
        try:
            # Try the newer OBS WebSocket API first
            current_scene = self.client.call(requests.GetCurrentProgramScene())
            print(f"📊 GetCurrentProgramScene response: {current_scene}")
            
            # Handle different response formats
            if hasattr(current_scene, 'sceneName'):
                return current_scene.sceneName
            elif hasattr(current_scene, 'getName'):
                return current_scene.getName()
            elif isinstance(current_scene, dict) and 'sceneName' in current_scene:
                return current_scene['sceneName']
            else:
                print(f"📊 Unexpected current scene response format: {type(current_scene)}, {current_scene}")
                return None
                
        except Exception as e:
            print(f"❌ GetCurrentProgramScene failed: {e}")
            # Fallback to older API
            try:
                current_scene = self.client.call(requests.GetCurrentScene())
                print(f"📊 GetCurrentScene (fallback) response: {current_scene}")
                
                if hasattr(current_scene, 'getName'):
                    return current_scene.getName()
                elif hasattr(current_scene, 'sceneName'):
                    return current_scene.sceneName
                elif isinstance(current_scene, dict) and 'sceneName' in current_scene:
                    return current_scene['sceneName']
                else:
                    print(f"📊 Unexpected fallback scene response format: {type(current_scene)}, {current_scene}")
                    return None
                    
            except Exception as fallback_error:
                print(f"❌ Error getting current OBS scene (both methods failed): {fallback_error}")
                return None
    
    def get_scene_list(self):
        """Get list of all scenes from OBS"""
        if not self.connected or not self.client:
            return []
        
        try:
            scene_list = self.client.call(requests.GetSceneList())
            return [scene['sceneName'] for scene in scene_list.getScenes()]
        except Exception as e:
            print(f"❌ Error getting OBS scene list: {e}")
            return []
    
    def _save_current_scene_to_storage(self, scene_name):
        """Save current scene to persistent storage file - MINIMAL VERSION (current scene only)"""
        if not scene_name or not isinstance(scene_name, str):
            raise ValueError(f"Invalid scene name for storage: {scene_name}")
            
        try:
            # Ensure scene name is clean
            scene_name = str(scene_name).strip()
            if not scene_name:
                raise ValueError("Scene name is empty after cleaning")
            
            current_scene_path = DATA_DIR / 'config' / 'obs_current_scene.json'
            
            # Simple data structure - only current scene and timestamp
            scene_data = {
                'current_scene': None,
                'last_updated': None
            }
            
            if current_scene_path.exists():
                try:
                    with open(current_scene_path, 'r', encoding='utf-8') as f:
                        loaded_data = json.load(f)
                        if isinstance(loaded_data, dict):
                            # Only preserve current_scene and last_updated, ignore scene_list
                            scene_data['current_scene'] = loaded_data.get('current_scene')
                            scene_data['last_updated'] = loaded_data.get('last_updated')
                        else:
                            print("⚠️ Invalid JSON structure in storage file, using defaults")
                except (json.JSONDecodeError, UnicodeDecodeError) as parse_error:
                    print(f"⚠️ Could not parse existing storage file: {parse_error}")
                    # Use default scene_data structure
                except Exception as file_error:
                    print(f"⚠️ Could not read existing storage file: {file_error}")
                    # Use default scene_data structure
            
            # Update current scene and timestamp only
            scene_data['current_scene'] = scene_name
            scene_data['last_updated'] = datetime.now().isoformat()
            
            # Ensure config directory exists
            try:
                config_dir = DATA_DIR / 'config'
                config_dir.mkdir(parents=True, exist_ok=True)
            except Exception as dir_error:
                print(f"❌ Could not create config directory: {dir_error}")
                raise
            
            # Save updated data with atomic write
            try:
                temp_path = current_scene_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(scene_data, f, indent=2, ensure_ascii=False)
                
                # Atomic rename to prevent corruption
                temp_path.replace(current_scene_path)
                
            except Exception as write_error:
                print(f"❌ Could not write to storage file: {write_error}")
                # Clean up temp file if it exists
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except:
                    pass
                raise
                
        except Exception as e:
            print(f"❌ CRITICAL: Storage save operation failed: {e}")
            raise  # Re-raise so caller can handle
    

    
    def enable_persistent_connection(self):
        """Enable persistent auto-reconnection to OBS"""
        print("🔄 Enabling persistent OBS connection...")
        self.auto_reconnect_enabled = True
        self.should_be_connected = True
        
        # If not connected, try to connect
        if not self.connected:
            if not self.settings:  # Only load settings if not already loaded
                if not self.load_settings():
                    print("❌ No OBS settings available for persistent connection")
                    return False
            
            print("🔌 Attempting OBS connection for persistent mode...")
            success = self.connect()
            if not success:
                print("⚠️  Initial connection failed, but will keep trying...")
        
        # Start connection monitor if not already running
        self._start_connection_monitor()
        return self.connected


def load_state():
    """Load the current state from state.json"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default state if file doesn't exist or is invalid
        default_state = {"current_animation": "anim1.html"}
        save_state(default_state)
        return default_state


def save_state(state):
    """Save the current state to state.json"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)


def ensure_state_file():
    """Initialize state file if it doesn't exist"""
    if not STATE_FILE.exists():
        save_state({"current_animation": "anim1.html"})


def get_animation_files():
    """Get list of all animation HTML files"""
    if not ANIMATIONS_DIR.exists():
        return []
    return sorted([f.name for f in ANIMATIONS_DIR.glob("*.html")])


def get_video_files():
    """Get list of all video files"""
    if not VIDEOS_DIR.exists():
        return []
    video_files = []
    for ext in VIDEO_EXTENSIONS:
        video_files.extend(VIDEOS_DIR.glob(f"*{ext}"))
    return sorted([f.name for f in video_files])


def get_all_media_files():
    """Get list of all supported media files (HTML animations + videos)"""
    animations = get_animation_files()
    videos = get_video_files()
    return sorted(animations + videos)


def is_video_file(filename):
    """Check if a filename has a video extension"""
    return Path(filename).suffix.lower() in VIDEO_EXTENSIONS


def is_html_file(filename):
    """Check if a filename has an HTML extension"""
    return Path(filename).suffix.lower() in HTML_EXTENSIONS


def find_media_file(filename):
    """Find a media file in either animations or videos directory"""
    # Try animations directory first
    animation_path = ANIMATIONS_DIR / filename
    if animation_path.exists():
        return animation_path, 'animation'
    
    # Try videos directory
    video_path = VIDEOS_DIR / filename
    if video_path.exists():
        return video_path, 'video'
    
    return None, None


@app.route('/')
def index():
    """Serve the current media (animation or video)"""
    state = load_state()
    current_media = state.get('current_animation', 'anim1.html')
    
    # Check if media file exists
    media_path, media_type = find_media_file(current_media)
    
    if not media_path:
        # Fallback to first available media or show error
        all_media = get_all_media_files()
        if all_media:
            current_media = all_media[0]
            state['current_animation'] = current_media
            save_state(state)
            media_path, media_type = find_media_file(current_media)
        else:
            return "No media files available. Please add HTML or video files to the animations/ or videos/ directories.", 404
    
    # Serve based on media type
    if media_type == 'video':
        return serve_video(current_media)
    else:
        # Serve HTML animation
        return send_from_directory(ANIMATIONS_DIR, current_media)


def serve_video(video_filename):
    """Serve a video file using the video player template"""
    video_path = VIDEOS_DIR / video_filename
    video_url = f"/videos/{video_filename}"
    
    # Determine video MIME type
    video_ext = Path(video_filename).suffix.lower()
    video_types = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.ogg': 'video/ogg',
        '.avi': 'video/avi',
        '.mov': 'video/quicktime',
        '.mkv': 'video/x-matroska'
    }
    video_type = video_types.get(video_ext, 'video/mp4')
    
    # Load and render the video player template
    try:
        with open('templates/video_player_template.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Simple template replacement (you could use Jinja2 for more complex templating)
        html_content = template_content.replace('{{ video_filename }}', video_filename)
        html_content = html_content.replace('{{ video_url }}', video_url)
        html_content = html_content.replace('{{ video_type }}', video_type)
        
        return html_content, 200, {'Content-Type': 'text/html'}
    
    except Exception as e:
        return f"Error loading video player template: {e}", 500


@app.route('/videos/<filename>')
def serve_video_file(filename):
    """Serve video files from the videos directory"""
    return send_from_directory(VIDEOS_DIR, filename)


@app.route('/mobile')
@app.route('/control')
def mobile_control():
    """Serve mobile stream control interface"""
    return render_template('mobile_control.html')


@app.route('/trigger', methods=['POST'])
def trigger():
    """Update the current media (animation or video) via JSON payload"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400
        
        media_file = data.get('animation')  # Keep 'animation' key for backwards compatibility
        if not media_file:
            return jsonify({"error": "Missing 'animation' field in payload"}), 400
        
        # Validate that the media file exists
        media_path, media_type = find_media_file(media_file)
        if not media_path:
            available_media = get_all_media_files()
            return jsonify({
                "error": f"Media file '{media_file}' not found",
                "available_media": available_media,
                "available_animations": get_animation_files(),
                "available_videos": get_video_files()
            }), 404
        
        # Update state
        state = load_state()
        state['current_animation'] = media_file
        save_state(state)

        # Emit animation change to all clients
        socketio.emit('animation_changed', {
            'current_animation': media_file,
            'media_type': media_type,
            'message': f"Media changed to '{media_file}' ({media_type})",
            'refresh_page': True
        })
        print(f"📡 [TRIGGER] Emitted 'animation_changed' for '{media_file}' with refresh_page=True")

        # Emit explicit page refresh
        socketio.emit('page_refresh', {
            'reason': 'media_changed',
            'new_media': media_file,
            'media_type': media_type
        })
        print(f"📡 [TRIGGER] Emitted 'page_refresh' for '{media_file}' - TV should reload now")

        return jsonify({
            "success": True,
            "current_animation": media_file,
            "media_type": media_type,
            "message": f"Media updated to '{media_file}' ({media_type})"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trigger', methods=['GET'])
def trigger_get():
    """Update the current media (animation or video) via GET with URL parameters"""
    try:
        media_file = request.args.get('animation')
        if not media_file:
            return jsonify({"error": "Missing 'animation' parameter"}), 400
        
        # Validate that the media file exists
        media_path, media_type = find_media_file(media_file)
        if not media_path:
            available_media = get_all_media_files()
            return jsonify({
                "error": f"Media file '{media_file}' not found",
                "available_media": available_media,
                "available_animations": get_animation_files(),
                "available_videos": get_video_files()
            }), 404
        
        # Update state
        state = load_state()
        state['current_animation'] = media_file
        save_state(state)

        # Emit animation change to all clients
        socketio.emit('animation_changed', {
            'current_animation': media_file,
            'media_type': media_type,
            'message': f"Media changed to '{media_file}' ({media_type}) via GET trigger",
            'refresh_page': True
        })

        # Emit explicit page refresh
        socketio.emit('page_refresh', {
            'reason': 'get_trigger',
            'new_media': media_file,
            'media_type': media_type
        })

        return jsonify({
            "success": True,
            "current_animation": media_file,
            "media_type": media_type,
            "message": f"Media updated to '{media_file}' ({media_type}) via GET"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/animations', methods=['GET'])
def list_animations():
    """List all available media files (animations and videos)"""
    animations = get_animation_files()
    videos = get_video_files()
    all_media = get_all_media_files()
    state = load_state()
    current_media = state.get('current_animation', None)
    
    return jsonify({
        "animations": animations,
        "videos": videos,
        "all_media": all_media,
        "current_animation": current_media,
        "current_media": current_media,  # Alternative key name
        "count": len(all_media),
        "animation_count": len(animations),
        "video_count": len(videos)
    }), 200


@app.route('/stop', methods=['POST'])
def stop_animations():
    """Stop all animations and clear current media"""
    try:
        state = load_state()
        state['current_animation'] = None
        
        # Save state
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Emit WebSocket event to notify all connected devices
        socketio.emit('animation_stopped', {
            'message': 'All animations stopped',
            'timestamp': time.time()
        })

        return jsonify({
            "success": True,
            "message": "All animations stopped"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "animations_available": len(get_animation_files()),
        "videos_available": len(get_video_files()),
        "total_media_available": len(get_all_media_files())
    }), 200


# WebSocket event handlers for OBS and StreamerBot integration

@socketio.on('connect')
def handle_connect():
    """Handle client WebSocket connection"""
    import time
    session_id = request.sid
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Determine device type based on referrer or user agent
    referrer = request.headers.get('Referer', '')
    device_type = 'admin' if '/admin' in referrer else 'tv'
    
    # Track connected device
    connected_devices[session_id] = {
        'type': device_type,
        'user_agent': user_agent,
        'connected_at': time.time()
    }
    
    if device_type == 'admin':
        admin_sessions.add(session_id)
    
    print(f"Client connected: {session_id} (type: {device_type})")
    
    # Broadcast device list update to admin clients
    socketio.emit('devices_updated', get_connected_devices_info(), room=None)
    
    emit('status', {
        'message': 'Connected to OBS-TV-Animator server',
        'current_animation': load_state().get('current_animation'),
        'available_animations': get_animation_files()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client WebSocket disconnection"""
    session_id = request.sid
    device_info = connected_devices.pop(session_id, {})
    admin_sessions.discard(session_id)
    
    device_type = device_info.get('type', 'unknown')
    print(f"Client disconnected: {session_id} (type: {device_type})")
    
    # Broadcast device list update to admin clients
    socketio.emit('devices_updated', get_connected_devices_info(), room=None)


@socketio.on('register_admin')
def handle_register_admin():
    """Register a client as admin dashboard"""
    session_id = request.sid
    if session_id in connected_devices:
        connected_devices[session_id]['type'] = 'admin'
        admin_sessions.add(session_id)
        print(f"Client {session_id} registered as admin dashboard")
        
        # Broadcast updated device list
        socketio.emit('devices_updated', get_connected_devices_info(), room=None)


@socketio.on('trigger_animation')
def handle_trigger_animation(data):
    """Handle animation trigger via WebSocket"""
    try:
        animation = data.get('animation')
        if not animation:
            emit('error', {'message': 'Missing animation field'})
            return
        
        # Validate media file exists
        media_path, media_type = find_media_file(animation)
        if not media_path:
            available_media = get_all_media_files()
            emit('error', {
                'message': f"Media file '{animation}' not found",
                'available_media': available_media
            })
            return
        
        # Update state
        state = load_state()
        old_animation = state.get('current_animation')
        state['current_animation'] = animation
        save_state(state)
        
        # Broadcast media change to all connected clients
        socketio.emit('animation_changed', {
            'previous_animation': old_animation,
            'current_animation': animation,
            'media_type': media_type,
            'message': f"Media changed to '{animation}' ({media_type})",
            'refresh_page': True  # Signal TV browsers to refresh
        }, broadcast=True)
        
        # Also send explicit page refresh command for TV browsers
        socketio.emit('page_refresh', {
            'reason': 'media_changed',
            'new_media': animation,
            'media_type': media_type
        }, broadcast=True)
        
        print(f"Animation changed from '{old_animation}' to '{animation}' via WebSocket")
        
    except Exception as e:
        emit('error', {'message': str(e)})
        print(f"WebSocket error: {e}")


@socketio.on('get_status')
def handle_get_status():
    """Get current server status via WebSocket"""
    state = load_state()
    current_media = state.get('current_animation')
    media_path, media_type = find_media_file(current_media) if current_media else (None, None)
    
    emit('status', {
        'current_animation': current_media,
        'current_media': current_media,
        'media_type': media_type,
        'available_animations': get_animation_files(),
        'available_videos': get_video_files(),
        'available_media': get_all_media_files(),
        'animations_count': len(get_animation_files()),
        'videos_count': len(get_video_files()),
        'total_media_count': len(get_all_media_files())
    })


@socketio.on('scene_change')
def handle_scene_change(data):
    """Handle OBS scene change event"""
    try:
        scene_name = data.get('scene_name', '').lower()
        animation_mapping = data.get('animation_mapping', {})
        
        # If specific mapping provided, use it
        if animation_mapping and scene_name in animation_mapping:
            animation = animation_mapping[scene_name]
        else:
            # Default scene-to-animation mapping
            default_mapping = {
                'gaming': 'anim1.html',
                'chatting': 'anim2.html',
                'brb': 'anim3.html',
                'be right back': 'anim3.html',
                'starting soon': 'anim1.html',
                'ending soon': 'anim2.html'
            }
            animation = default_mapping.get(scene_name)
        
        if animation:
            # Trigger animation change
            handle_trigger_animation({'animation': animation})
        else:
            emit('info', {
                'message': f"No animation mapping for scene '{data.get('scene_name')}'"
            })
            
    except Exception as e:
        emit('error', {'message': f"Scene change error: {str(e)}"})
        print(f"Scene change error: {e}")


@socketio.on('streamerbot_event')
def handle_streamerbot_event(data):
    """Handle StreamerBot events"""
    try:
        event_type = data.get('event_type')
        event_data = data.get('data', {})
        
        print(f"StreamerBot event received: {event_type}")
        
        # Handle different StreamerBot event types
        if event_type == 'scene_change':
            handle_scene_change(event_data)
        elif event_type == 'trigger_animation':
            handle_trigger_animation(event_data)
        elif event_type == 'custom_animation':
            # Custom event with animation specified
            animation = event_data.get('animation')
            if animation:
                handle_trigger_animation({'animation': animation})
        else:
            emit('info', {'message': f"Unhandled StreamerBot event: {event_type}"})
            
    except Exception as e:
        emit('error', {'message': f"StreamerBot event error: {str(e)}"})
        print(f"StreamerBot event error: {e}")


@socketio.on('video_control')
def handle_video_control(data):
    """Handle video playback control commands"""
    try:
        action = data.get('action')
        value = data.get('value')
        
        if not action:
            emit('error', {'message': 'Missing action for video control'})
            return
        
        # Validate current media is a video
        state = load_state()
        current_media = state.get('current_animation')
        if current_media and not is_video_file(current_media):
            emit('error', {'message': 'Current media is not a video file'})
            return
        
        # Broadcast video control to all connected clients (including the TV)
        socketio.emit('video_control', {
            'action': action,
            'value': value,
            'message': f"Video control: {action}"
        }, broadcast=True)
        
        print(f"Video control: {action} {f'({value})' if value is not None else ''}")
        
    except Exception as e:
        emit('error', {'message': f"Video control error: {str(e)}"})
        print(f"Video control error: {e}")


@socketio.on('video_seek')
def handle_video_seek(data):
    """Handle video seek commands"""
    try:
        time = data.get('time', 0)
        
        # Broadcast seek command
        socketio.emit('video_control', {
            'action': 'seek',
            'value': time,
            'message': f"Video seek to {time}s"
        }, broadcast=True)
        
        print(f"Video seek to {time}s")
        
    except Exception as e:
        emit('error', {'message': f"Video seek error: {str(e)}"})
        print(f"Video seek error: {e}")


@socketio.on('video_volume')
def handle_video_volume(data):
    """Handle video volume control"""
    try:
        volume = data.get('volume', 0.5)
        volume = max(0, min(1, float(volume)))  # Clamp between 0 and 1
        
        # Broadcast volume change
        socketio.emit('video_control', {
            'action': 'volume',
            'value': volume,
            'message': f"Video volume set to {int(volume * 100)}%"
        }, broadcast=True)
        
        print(f"Video volume set to {int(volume * 100)}%")
        
    except Exception as e:
        emit('error', {'message': f"Video volume error: {str(e)}"})
        print(f"Video volume error: {e}")


# Raw WebSocket Server for StreamerBot Integration
class RawWebSocketServer:
    def __init__(self, port=8081):
        self.port = port
        self.clients = set()
        self.server = None
        
    async def handle_client(self, websocket, path):
        """Handle incoming raw WebSocket connections from StreamerBot"""
        print(f"Raw WebSocket client connected from {websocket.remote_address}")
        self.clients.add(websocket)
        
        try:
            async for message in websocket:
                try:
                    # Parse the incoming message
                    data = json.loads(message)
                    print(f"Raw WebSocket message received: {data}")
                    
                    # Handle different message types
                    if data.get('action') == 'trigger_animation':
                        animation = data.get('animation')
                        # Optional control flags from StreamerBot
                        instant = data.get('instant', True)  # Default to instant
                        force_refresh = data.get('force_refresh', True)  # Default to force refresh
                        source_name = data.get('source', 'streamerbot_websocket')
                        
                        if animation:
                            # Validate the animation file exists
                            media_path, media_type = find_media_file(animation)
                            if not media_path:
                                available_media = get_all_media_files()
                                error_response = {
                                    'status': 'error',
                                    'message': f'Animation file not found: {animation}',
                                    'available_media': available_media
                                }
                                await websocket.send(json.dumps(error_response))
                                continue
                            
                            # Update the current animation state
                            state = load_state()
                            old_animation = state.get('current_animation')
                            state['current_animation'] = animation
                            save_state(state)
                            
                            # Determine media type
                            media_type = "video" if is_video_file(animation) else "animation"
                            
                            # Broadcast to all Socket.IO clients (TV displays)
                            socketio.emit('animation_changed', {
                                'previous_animation': old_animation,
                                'current_animation': animation,
                                'media_type': media_type,
                                'message': f"Media changed to '{animation}' ({media_type}) via StreamerBot WebSocket",
                                'refresh_page': force_refresh,
                                'instant': instant,
                                'source': source_name
                            })
                            
                            # Send page refresh command for instant TV browser updates
                            if force_refresh:
                                socketio.emit('page_refresh', {
                                    'animation': animation,
                                    'instant': instant,
                                    'source': source_name
                                })
                            
                            # Send confirmation back to StreamerBot
                            response = {
                                'status': 'success',
                                'message': f'Animation changed to {animation}',
                                'animation': animation,
                                'instant': instant,
                                'force_refresh': force_refresh,
                                'media_type': media_type
                            }
                            await websocket.send(json.dumps(response))
                            print(f"StreamerBot: Animation changed to {animation}")
                        else:
                            error_response = {
                                'status': 'error',
                                'message': 'Missing animation parameter'
                            }
                            await websocket.send(json.dumps(error_response))
                    
                    elif data.get('action') == 'get_status':
                        # Send current status
                        state = load_state()
                        status_response = {
                            'status': 'success',
                            'current_animation': state.get('current_animation'),
                            'connected_devices': len(connected_devices),
                            'server_version': __version__
                        }
                        await websocket.send(json.dumps(status_response))
                        
                    else:
                        # Unknown action type
                        error_response = {
                            'status': 'error',
                            'message': f'Unknown action type: {data.get("action")}'
                        }
                        await websocket.send(json.dumps(error_response))
                        
                except json.JSONDecodeError:
                    error_response = {
                        'status': 'error',
                        'message': 'Invalid JSON format'
                    }
                    await websocket.send(json.dumps(error_response))
                except Exception as e:
                    error_response = {
                        'status': 'error',
                        'message': f'Server error: {str(e)}'
                    }
                    await websocket.send(json.dumps(error_response))
                    print(f"Raw WebSocket error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"Raw WebSocket client disconnected: {websocket.remote_address}")
        except Exception as e:
            print(f"Raw WebSocket handler error: {e}")
        finally:
            self.clients.discard(websocket)
    
    def start_server(self):
        """Start the raw WebSocket server in a separate thread"""
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                start_server = websockets.serve(
                    self.handle_client, 
                    "0.0.0.0", 
                    self.port,
                    ping_interval=20,
                    ping_timeout=10
                )
                
                print(f"Raw WebSocket server starting on port {self.port} for StreamerBot...")
                loop.run_until_complete(start_server)
                loop.run_forever()
            except Exception as e:
                print(f"Raw WebSocket server error: {e}")
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        return thread

# Initialize the raw WebSocket server
raw_websocket_server = RawWebSocketServer(port=WEBSOCKET_PORT)


# Admin interface routes

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    error = None
    username = None
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            error = "Please enter both username and password."
        elif verify_password(username, password):
            user = User(username)
            login_user(user, remember=remember)
            
            # Update last login timestamp
            try:
                users_data = load_users_config()
                if username in users_data.get('admin_users', {}):
                    users_data['admin_users'][username]['last_login'] = datetime.now().isoformat()
                    save_users_config(users_data)
            except Exception as e:
                print(f"Error updating last login for {username}: {e}")
            
            # Check if logging in with default credentials
            if username == 'admin' and password == 'admin123':
                session['show_default_credentials_warning'] = True
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/admin'):
                return redirect(next_page)
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Invalid username or password."
    
    return render_template('admin_login.html', error=error, username=username)

@app.route('/admin/logout')
@admin_required
def admin_logout():
    """Admin logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard for managing animations and monitoring status"""
    # Get user's theme preference
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        user_theme = user_data.get('theme', 'dark')  # Default to dark
        print(f"Dashboard: User '{current_user.username}' theme is '{user_theme}'")
    except Exception as e:
        print(f"Dashboard: Error loading theme: {e}")
        user_theme = 'dark'  # Fallback to dark theme
    
    # Check for default credentials warning
    show_credentials_warning = session.pop('show_default_credentials_warning', False)
    
    return render_template('admin_dashboard.html', 
                         user_theme=user_theme,
                         current_username=current_user.username,
                         show_credentials_warning=show_credentials_warning,
                         app_version=__version__)


@app.route('/admin/manage')
@admin_required
def admin_manage_files():
    """File management page for uploading/deleting animations"""
    # Get user's theme preference
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        user_theme = user_data.get('theme', 'dark')  # Default to dark
    except Exception:
        user_theme = 'dark'  # Fallback to dark theme
    
    return render_template('admin_manage.html', 
                         user_theme=user_theme,
                         current_username=current_user.username,
                         app_version=__version__)


@app.route('/admin/users')
@admin_required
def admin_users():
    """User management page"""
    # Get user's theme preference
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        user_theme = user_data.get('theme', 'dark')  # Default to dark
    except Exception:
        user_theme = 'dark'  # Fallback to dark theme
    
    return render_template('admin_users.html', 
                         user_theme=user_theme,
                         current_username=current_user.username,
                         app_version=__version__)


@app.route('/admin/obs')
@admin_required
def admin_obs_management():
    """OBS WebSocket management page"""
    # Get user's theme preference
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        user_theme = user_data.get('theme', 'dark')  # Default to dark
    except Exception:
        user_theme = 'dark'  # Fallback to dark theme
    
    return render_template('admin_obs_management.html', 
                         user_theme=user_theme,
                         current_username=current_user.username,
                         app_version=__version__)


@app.route('/admin/instructions')
@admin_required
def admin_instructions():
    """Instructions and setup page"""
    # Get user's theme preference
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        user_theme = user_data.get('theme', 'dark')  # Default to dark
    except Exception:
        user_theme = 'dark'  # Fallback to dark theme
    
    return render_template('admin_instructions.html', 
                         user_theme=user_theme,
                         current_username=current_user.username,
                         app_version=__version__)


@app.route('/admin/instructions/getting-started')
@admin_required
def admin_instructions_getting_started():
    """Getting Started instructions page"""
    # Get user's theme preference
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        user_theme = user_data.get('theme', 'dark')  # Default to dark
    except Exception:
        user_theme = 'dark'  # Fallback to dark theme
    
    return render_template('admin_instructions_getting_started.html', 
                         user_theme=user_theme,
                         current_username=current_user.username,
                         app_version=__version__)


@app.route('/admin/instructions/obs-integration')
@admin_required
def admin_instructions_obs():
    """OBS Studio Integration instructions page"""
    # Get user's theme preference
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        user_theme = user_data.get('theme', 'dark')  # Default to dark
    except Exception:
        user_theme = 'dark'  # Fallback to dark theme
    
    return render_template('admin_instructions_obs.html', 
                         user_theme=user_theme,
                         current_username=current_user.username,
                         app_version=__version__)


@app.route('/admin/instructions/streamerbot-integration')
@admin_required
def admin_instructions_streamerbot():
    """StreamerBot Integration instructions page"""
    # Get user's theme preference
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        user_theme = user_data.get('theme', 'dark')  # Default to dark
    except Exception:
        user_theme = 'dark'  # Fallback to dark theme
    
    return render_template('admin_instructions_streamerbot.html', 
                         user_theme=user_theme,
                         current_username=current_user.username,
                         app_version=__version__)


@app.route('/admin/instructions/troubleshooting')
@admin_required
def admin_instructions_troubleshooting():
    """Troubleshooting & FAQ instructions page"""
    # Get user's theme preference
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        user_theme = user_data.get('theme', 'dark')  # Default to dark
    except Exception:
        user_theme = 'dark'  # Fallback to dark theme
    
    return render_template('admin_instructions_troubleshooting.html', 
                         user_theme=user_theme,
                         current_username=current_user.username,
                         app_version=__version__)


def save_users_config(users_data):
    """Save users configuration to file"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving users config: {e}")
        return False


@app.route('/admin/api/users', methods=['GET'])
@admin_required
def api_get_users():
    """API endpoint to get list of users"""
    try:
        users_data = load_users_config()
        admin_users = users_data.get('admin_users', {})
        
        user_list = []
        for username, user_info in admin_users.items():
            user_list.append({
                'username': username,
                'created_at': user_info.get('created_at'),
                'last_login': user_info.get('last_login'),
                'permissions': user_info.get('permissions', [])
            })
        
        return jsonify({
            'success': True,
            'users': user_list,
            'current_user': current_user.username
        })
    
    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/users', methods=['POST'])
@admin_required
def api_add_user():
    """API endpoint to add new user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password are required'}), 400
        
        if len(username) < 3:
            return jsonify({'success': False, 'error': 'Username must be at least 3 characters long'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters long'}), 400
        
        users_data = load_users_config()
        admin_users = users_data.get('admin_users', {})
        
        if username in admin_users:
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        # Add new user
        admin_users[username] = {
            'password': password,  # In production, hash this!
            'created_at': datetime.now().isoformat(),
            'permissions': ['read', 'write', 'delete', 'upload'],
            'theme': 'dark'  # Default theme
        }
        
        users_data['admin_users'] = admin_users
        
        if save_users_config(users_data):
            return jsonify({'success': True, 'message': f'User {username} added successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save user data'}), 500
    
    except Exception as e:
        print(f"Error adding user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/users', methods=['DELETE'])
@admin_required
def api_delete_user():
    """API endpoint to delete user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'success': False, 'error': 'Username is required'}), 400
        
        if username == current_user.username:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        users_data = load_users_config()
        admin_users = users_data.get('admin_users', {})
        
        if username not in admin_users:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Prevent deleting the last remaining user
        if len(admin_users) <= 1:
            return jsonify({'success': False, 'error': 'Cannot delete the last remaining user'}), 400
        
        # Delete user
        del admin_users[username]
        users_data['admin_users'] = admin_users
        
        if save_users_config(users_data):
            return jsonify({'success': True, 'message': f'User {username} deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save user data'}), 500
    
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/change-password', methods=['POST'])
@admin_required
def api_change_password():
    """API endpoint to change current user's password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Current and new passwords are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'New password must be at least 6 characters long'}), 400
        
        # Verify current password
        if not verify_password(current_user.username, current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
        
        users_data = load_users_config()
        admin_users = users_data.get('admin_users', {})
        
        if current_user.username not in admin_users:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Update password
        admin_users[current_user.username]['password'] = new_password  # In production, hash this!
        users_data['admin_users'] = admin_users
        
        if save_users_config(users_data):
            return jsonify({'success': True, 'message': 'Password changed successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save password change'}), 500
    
    except Exception as e:
        print(f"Error changing password: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/status')
@api_admin_required
def admin_status():
    """API endpoint for admin dashboard status"""
    try:
        state = load_state()
        current_media = state.get('current_animation')
        media_path, media_type = find_media_file(current_media) if current_media else (None, None)
        
        # Get device information
        devices_info = get_connected_devices_info()
        
        # Get OBS connection status
        obs_connected = False
        if obs_client:
            obs_connected = obs_client.connected
        
        return jsonify({
            'status': 'running',
            'current_media': current_media,
            'media_type': media_type,
            'animations_count': len(get_animation_files()),
            'videos_count': len(get_video_files()),
            'total_media_count': len(get_all_media_files()),
            'connected_clients': devices_info['tv_count'],  # Only count TV devices, not admin
            'tv_devices': devices_info['tv_devices'],
            'admin_count': devices_info['admin_count'],
            'streamerbot_devices': devices_info['streamerbot_devices'],
            'streamerbot_count': devices_info['streamerbot_count'],
            'total_connections': devices_info['total_count'],
            'available_animations': get_animation_files(),
            'available_videos': get_video_files(),
            'available_media': get_all_media_files(),
            'obs_connected': obs_connected
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/files')
@api_admin_required
def admin_list_files():
    """API endpoint to list all files with metadata"""
    try:
        files = []
        
        # Add animation files
        for filename in get_animation_files():
            file_path = ANIMATIONS_DIR / filename
            files.append({
                'name': filename,
                'type': 'animation',
                'size': file_path.stat().st_size if file_path.exists() else 0,
                'url': f'/animations/{filename}',
                'thumbnail': f'/admin/api/thumbnail/{filename}'
            })
        
        # Add video files
        for filename in get_video_files():
            file_path = VIDEOS_DIR / filename
            files.append({
                'name': filename,
                'type': 'video',
                'size': file_path.stat().st_size if file_path.exists() else 0,
                'url': f'/videos/{filename}',
                'thumbnail': f'/admin/api/thumbnail/{filename}'
            })
        
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/files')
def list_files():
    """Public API endpoint to list all files for mobile interface"""
    try:
        files = []
        
        # Add animation files
        for filename in get_animation_files():
            file_path = ANIMATIONS_DIR / filename
            files.append({
                'name': filename,
                'type': 'animation',
                'size': file_path.stat().st_size if file_path.exists() else 0,
                'url': f'/animations/{filename}',
                'thumbnail': f'/admin/api/thumbnail/{filename}'
            })
        
        # Add video files  
        for filename in get_video_files():
            file_path = VIDEOS_DIR / filename
            files.append({
                'name': filename,
                'type': 'video',
                'size': file_path.stat().st_size if file_path.exists() else 0,
                'url': f'/videos/{filename}',
                'thumbnail': f'/admin/api/thumbnail/{filename}'
            })
        
        # Get current animation state
        state = load_state()
        current_animation = state.get('current_animation', None)
        
        return jsonify({
            'files': files,
            'current_animation': current_animation
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/upload', methods=['POST'])
@admin_required
def admin_upload_file():
    """Handle file uploads for animations and videos"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = file.filename
        file_ext = Path(filename).suffix.lower()
        
        # Determine file type and destination
        if file_ext in HTML_EXTENSIONS:
            destination_dir = ANIMATIONS_DIR
            file_type = 'animation'
        elif file_ext in VIDEO_EXTENSIONS:
            destination_dir = VIDEOS_DIR
            file_type = 'video'
        else:
            return jsonify({
                'error': f'Unsupported file type: {file_ext}',
                'supported_types': list(HTML_EXTENSIONS | VIDEO_EXTENSIONS)
            }), 400
        
        # Ensure destination directory exists
        destination_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = destination_dir / filename
        file.save(str(file_path))
        
        # Generate thumbnail asynchronously
        try:
            thumbnail_service = get_thumbnail_service(f"http://localhost:{get_current_port()}")
            
            def generate_thumbnail_background():
                """Generate thumbnail in background thread"""
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success, thumbnail_name = loop.run_until_complete(
                        thumbnail_service.generate_thumbnail(filename, file_path)
                    )
                    loop.close()
                    
                    if success:
                        app.logger.info(f"Generated thumbnail for uploaded file: {filename}")
                    else:
                        app.logger.warning(f"Failed to generate thumbnail for uploaded file: {filename}")
                        
                except Exception as e:
                    app.logger.error(f"Thumbnail generation error for {filename}: {str(e)}")
            
            # Start thumbnail generation in background thread
            Thread(target=generate_thumbnail_background, daemon=True).start()
            
        except Exception as e:
            app.logger.warning(f"Could not start thumbnail generation for {filename}: {str(e)}")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'file_type': file_type,
            'size': file_path.stat().st_size,
            'message': f'File {filename} uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/delete/<file_type>/<filename>', methods=['DELETE'])
@admin_required
def admin_delete_file(file_type, filename):
    """Delete a file (animation or video)"""
    try:
        if file_type == 'animation':
            file_path = ANIMATIONS_DIR / filename
        elif file_type == 'video':
            file_path = VIDEOS_DIR / filename
        else:
            return jsonify({'error': 'Invalid file type'}), 400
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Check if it's the current media
        state = load_state()
        current_media = state.get('current_animation')
        if current_media == filename:
            return jsonify({'error': 'Cannot delete currently active media'}), 400
        
        # Delete file
        file_path.unlink()
        
        # Clean up thumbnail if it exists
        try:
            thumbnail_service = get_thumbnail_service(f"http://localhost:{get_current_port()}")
            # Use get_thumbnail_path directly for more reliable deletion
            thumbnail_path = thumbnail_service.get_thumbnail_path(filename)
            if thumbnail_path.exists():
                thumbnail_path.unlink()
                app.logger.info(f"Deleted thumbnail for: {filename}")
        except Exception as e:
            app.logger.warning(f"Could not delete thumbnail for {filename}: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'File {filename} deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/thumbnail/<filename>')
@admin_required
def admin_thumbnail(filename):
    """Generate or serve thumbnails for files"""
    try:
        # Get the thumbnail service
        thumbnail_service = get_thumbnail_service(f"http://localhost:{get_current_port()}")
        
        # Try to serve existing thumbnail
        thumbnail_path = thumbnail_service.serve_thumbnail(filename)
        if thumbnail_path:
            return send_from_directory(
                str(thumbnail_path.parent), 
                thumbnail_path.name,
                mimetype='image/png'
            )
        
        # If no thumbnail exists, try to generate one
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext in ['html', 'htm']:
            # Check if HTML file exists
            html_path = Path(ANIMATIONS_DIR) / filename
            if html_path.exists():
                # Generate thumbnail asynchronously
                try:
                    # Create event loop for async thumbnail generation
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success, thumbnail_name = loop.run_until_complete(
                        thumbnail_service.generate_thumbnail(filename, html_path)
                    )
                    loop.close()
                    
                    if success:
                        # Serve the newly generated thumbnail
                        thumbnail_path = thumbnail_service.serve_thumbnail(filename)
                        if thumbnail_path:
                            return send_from_directory(
                                str(thumbnail_path.parent), 
                                thumbnail_path.name,
                                mimetype='image/png'
                            )
                except Exception as e:
                    app.logger.warning(f"Failed to generate HTML thumbnail for {filename}: {str(e)}")
        
        elif file_ext in ['mp4', 'webm', 'mov', 'avi', 'mkv']:
            # Check if video file exists
            video_path = Path(VIDEOS_DIR) / filename
            if video_path.exists():
                # Generate thumbnail synchronously (FFmpeg)
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success, thumbnail_name = loop.run_until_complete(
                        thumbnail_service.generate_thumbnail(filename, video_path)
                    )
                    loop.close()
                    
                    if success:
                        # Serve the newly generated thumbnail
                        thumbnail_path = thumbnail_service.serve_thumbnail(filename)
                        if thumbnail_path:
                            return send_from_directory(
                                str(thumbnail_path.parent), 
                                thumbnail_path.name,
                                mimetype='image/png'
                            )
                except Exception as e:
                    app.logger.warning(f"Failed to generate video thumbnail for {filename}: {str(e)}")
        
        # Fallback to SVG placeholders if thumbnail generation fails
        if file_ext in ['html', 'htm']:
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="320" height="180" xmlns="http://www.w3.org/2000/svg">
  <rect width="320" height="180" fill="#2c3e50"/>
  <text x="160" y="95" text-anchor="middle" fill="white" font-family="Arial" font-size="16">{filename[:25]}{'...' if len(filename) > 25 else ''}</text>
  <text x="160" y="115" text-anchor="middle" fill="#bdc3c7" font-family="Arial" font-size="12">HTML Animation</text>
</svg>'''
            return svg_content, 200, {'Content-Type': 'image/svg+xml'}
        
        else:
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="320" height="180" xmlns="http://www.w3.org/2000/svg">
  <rect width="320" height="180" fill="#34495e"/>
  <polygon points="140,70 140,110 180,90" fill="white"/>
  <text x="160" y="135" text-anchor="middle" fill="white" font-family="Arial" font-size="14">{filename[:25]}{'...' if len(filename) > 25 else ''}</text>
  <text x="160" y="155" text-anchor="middle" fill="#bdc3c7" font-family="Arial" font-size="10">Video File</text>
</svg>'''
            return svg_content, 200, {'Content-Type': 'image/svg+xml'}
        
    except Exception as e:
        app.logger.error(f"Thumbnail generation error for {filename}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/thumbnails/generate', methods=['POST'])
@admin_required
def admin_generate_thumbnails():
    """Generate thumbnails for all files"""
    try:
        thumbnail_service = get_thumbnail_service(f"http://localhost:{get_current_port()}")
        
        def generate_all_thumbnails():
            """Generate thumbnails for all files in background"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                results = loop.run_until_complete(
                    thumbnail_service.generate_all_thumbnails(
                        Path(ANIMATIONS_DIR), 
                        Path(VIDEOS_DIR)
                    )
                )
                
                loop.close()
                
                # Log results
                app.logger.info(f"Thumbnail generation complete: {results}")
                
                # Cleanup orphaned thumbnails
                cleaned_count = thumbnail_service.cleanup_orphaned_thumbnails(
                    Path(ANIMATIONS_DIR), 
                    Path(VIDEOS_DIR)
                )
                results['orphaned_cleaned'] = cleaned_count
                
                return results
                
            except Exception as e:
                app.logger.error(f"Bulk thumbnail generation failed: {str(e)}")
                return {'error': str(e)}
        
        # Start generation in background thread
        Thread(target=generate_all_thumbnails, daemon=True).start()
        
        return jsonify({
            'success': True,
            'message': 'Thumbnail generation started in background'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/thumbnails/status', methods=['GET'])
@admin_required
def admin_thumbnails_status():
    """Get thumbnail generation status"""
    try:
        thumbnail_service = get_thumbnail_service(f"http://localhost:{get_current_port()}")
        
        # Count existing thumbnails
        thumbnail_count = len(list(thumbnail_service.thumbnails_dir.glob('*.png')))
        
        # Count files that need thumbnails
        html_files = list(Path(ANIMATIONS_DIR).glob('*.html')) if Path(ANIMATIONS_DIR).exists() else []
        video_extensions = ['*.mp4', '*.webm', '*.mov', '*.avi', '*.mkv']
        video_files = []
        
        if Path(VIDEOS_DIR).exists():
            for pattern in video_extensions:
                video_files.extend(list(Path(VIDEOS_DIR).glob(pattern)))
        
        total_files = len(html_files) + len(video_files)
        
        # Check which files have thumbnails
        files_with_thumbnails = 0
        for html_file in html_files:
            if thumbnail_service.thumbnail_exists(html_file.name, html_file):
                files_with_thumbnails += 1
        
        for video_file in video_files:
            if thumbnail_service.thumbnail_exists(video_file.name, video_file):
                files_with_thumbnails += 1
        
        return jsonify({
            'total_files': total_files,
            'html_files': len(html_files),
            'video_files': len(video_files),
            'thumbnail_count': thumbnail_count,
            'files_with_thumbnails': files_with_thumbnails,
            'completion_percentage': round((files_with_thumbnails / total_files * 100) if total_files > 0 else 100, 1)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/thumbnails/debug', methods=['GET'])
@admin_required
def admin_thumbnails_debug():
    """Debug endpoint to list actual thumbnail files"""
    try:
        thumbnail_service = get_thumbnail_service(f"http://localhost:{get_current_port()}")
        
        # List all PNG files in thumbnails directory
        thumbnail_files = list(thumbnail_service.thumbnails_dir.glob('*.png'))
        
        debug_info = {
            'thumbnails_directory': str(thumbnail_service.thumbnails_dir),
            'directory_exists': thumbnail_service.thumbnails_dir.exists(),
            'thumbnail_files': [
                {
                    'filename': f.name,
                    'size_bytes': f.stat().st_size if f.exists() else 0,
                    'modified': f.stat().st_mtime if f.exists() else 0
                } for f in thumbnail_files
            ],
            'total_thumbnails': len(thumbnail_files)
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Theme Management API
@app.route('/admin/api/theme', methods=['GET'])
@admin_required
def get_user_theme():
    """Get current user's theme preference"""
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        theme = user_data.get('theme', 'dark')  # Default to dark
        return jsonify({'theme': theme})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/theme', methods=['POST'])
@admin_required
def save_user_theme():
    """Save current user's theme preference"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        theme = data.get('theme', 'dark')
        print(f"Saving theme '{theme}' for user '{current_user.username}'")
        
        # Validate theme value
        if theme not in ['light', 'dark']:
            return jsonify({'error': 'Invalid theme. Must be "light" or "dark"'}), 400
        
        # Load current users config
        users_data = load_users_config()
        print(f"Loaded users data: {users_data}")
        
        # Update user's theme preference
        if current_user.username in users_data.get('admin_users', {}):
            users_data['admin_users'][current_user.username]['theme'] = theme
            print(f"Updated user theme to: {theme}")
            
            # Save back to file with proper formatting
            try:
                with open(USERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(users_data, f, indent=4, ensure_ascii=False)
                print(f"Successfully saved theme to {USERS_FILE}")
                
                return jsonify({'success': True, 'theme': theme})
            except Exception as write_error:
                print(f"Error writing to file: {write_error}")
                return jsonify({'error': f'Failed to save theme: {write_error}'}), 500
        else:
            print(f"User '{current_user.username}' not found in admin_users")
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        print(f"Error in save_user_theme: {e}")
        return jsonify({'error': str(e)}), 500


# Debug endpoint to check user data
@app.route('/admin/api/debug/user')
@admin_required
def debug_user_data():
    """Debug endpoint to check current user data"""
    try:
        users_data = load_users_config()
        user_data = users_data.get('admin_users', {}).get(current_user.username, {})
        return jsonify({
            'username': current_user.username,
            'user_data': user_data,
            'theme': user_data.get('theme', 'NOT_SET')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Ensure required directories exist
    ANIMATIONS_DIR.mkdir(exist_ok=True)
    VIDEOS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    CONFIG_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Initialize state file if it doesn't exist
    if not STATE_FILE.exists():
        save_state({"current_animation": "anim1.html"})
    
    # Initialize users config if it doesn't exist
    if not USERS_FILE.exists():
        default_users = {
            "admin_users": {
                "admin": {
                    "password": "admin123",
                    "created_at": datetime.now().isoformat(),
                    "permissions": ["read", "write", "delete", "upload"],
                    "theme": "dark"
                }
            },
            "session_config": {
                "timeout_minutes": 60,
                "remember_me_days": 7
            }
        }
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_users, f, indent=2)
    
    # Run the Flask-SocketIO server on all interfaces (0.0.0.0) port 8080
    print("OBS-TV-Animator WebSocket Server Starting...")
    print("=" * 84)
    print(f"Available animations: {get_animation_files()}")
    print(f"Available videos: {get_video_files()}")
    print("=" * 84)
    print("🌐 HTTP API Routes:")
    print("  GET  /               - Smart TV display (main animation endpoint)")
    print("  GET  /admin          - Admin dashboard and file management")
    print("  POST /trigger        - Update media via API (JSON: {\"animation\": \"file.html|mp4\"})")
    print("  GET  /animations     - List available media files")
    print("  GET  /health         - Health check endpoint")
    print("=" * 84)
    print("🔌 WebSocket Integration:")
    print(f"  Socket.IO (port {MAIN_PORT}) - Real-time communication")
    print("    • Admin dashboard updates")
    print("    • Animation page refresh & status")
    print("    • OTA Integration (/static/js/ota-integration.js)")
    print(f"  Raw WebSocket (port {WEBSOCKET_PORT}) - StreamerBot compatibility")
    print("    • Legacy integration support")
    print("=" * 84)
    print("📁 Media Storage:")
    print(f"  Animations: {ANIMATIONS_DIR} ({len(get_animation_files())} files)")
    print(f"  Videos: {VIDEOS_DIR} ({len(get_video_files())} files)")
    print(f"  Data: {DATA_DIR} (users, settings, thumbnails)")
    print("=" * 84)
    print("🤖 StreamerBot Integration:")
    print("  • Use 'StreamerBot C#' buttons in admin file management")
    print("  • Copy ready-to-use C# code for each animation")
    print("  • HTTP triggers also available for legacy setups")
    print("  • Visit /admin/instructions/streamerbot-integration for setup guide")
    print("=" * 84)
    print("✨ Custom Animation Development:")
    print("  • Add OTA Integration to your HTML files:")
    print("    <link rel=\"stylesheet\" href=\"/static/css/ota-integration.css\">")
    print("    <script src=\"/static/js/ota-integration.js\"></script>")
    print("  • Enables status indicators, WebSocket sync, and page refresh")
    print("  • Visit /admin/instructions/getting-started for complete guide")
    print("=" * 84)


# =============================================================================
# OBS WebSocket API Routes
# =============================================================================

@app.route('/api/obs/settings', methods=['GET'])
@admin_required
def api_obs_settings_get():
    """Get OBS connection settings"""
    try:
        # Create config path if it doesn't exist
        obs_config_path = DATA_DIR / 'config' / 'obs_settings.json'
        
        if obs_config_path.exists():
            with open(obs_config_path, 'r') as f:
                settings = json.load(f)
        else:
            # Default settings
            settings = {
                'host': 'localhost',
                'port': 4455,
                'password': '',
                'enabled': True
            }
        
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/obs/settings', methods=['POST'])
@admin_required
def api_obs_settings_post():
    """Save OBS connection settings"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        settings = {
            'host': data.get('host', 'localhost'),
            'port': int(data.get('port', 4455)),
            'password': data.get('password', ''),
            'enabled': data.get('enabled', True)
        }
        
        # Ensure config directory exists
        config_dir = DATA_DIR / 'config'
        config_dir.mkdir(exist_ok=True)
        
        # Save settings
        obs_config_path = config_dir / 'obs_settings.json'
        with open(obs_config_path, 'w') as f:
            json.dump(settings, f, indent=2)
        
        # Check if we need to restart the OBS client
        global obs_client
        needs_restart = False
        
        # Check if settings actually changed significantly
        if obs_client and obs_client.settings:
            old_settings = obs_client.settings
            if (old_settings.get('host') != settings['host'] or 
                old_settings.get('port') != settings['port'] or 
                old_settings.get('password') != settings['password']):
                needs_restart = True
                print(f"🔄 Connection settings changed, restart required")
        else:
            needs_restart = True
            print(f"🔄 No existing client or settings, initial connection required")
        
        if needs_restart:
            print(f"🔄 Restarting OBS client with new settings...")
            
            # Disconnect old client if it exists (force because we're changing settings)
            if obs_client:
                try:
                    obs_client.disconnect(permanent=True, force=True)
                except:
                    pass
            
            # Create new client and load the fresh settings
            obs_client = OBSWebSocketClient()
        
        # Always ensure connection if enabled (whether restart or not)
        if settings.get('enabled', True):
            print(f"🔄 OBS connection enabled, ensuring persistent connection...")
            if obs_client:
                obs_client.enable_persistent_connection()
                connected = obs_client.connected
                print(f"🔄 Connection result: {connected}")
            else:
                connected = False
        else:
            print(f"🔄 OBS connection disabled in settings")
            if obs_client:
                obs_client.disconnect(permanent=True, force=True)  # Force because user disabled it
            connected = False
        
        return jsonify({'success': True, 'auto_connected': connected, 'enabled': settings.get('enabled', True)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/obs/mappings', methods=['GET'])
@admin_required
def api_obs_mappings_get():
    """Get scene to animation mappings"""
    try:
        # Create config path if it doesn't exist
        mappings_path = DATA_DIR / 'config' / 'obs_mappings.json'
        
        if mappings_path.exists():
            with open(mappings_path, 'r') as f:
                content = f.read().strip()
                if content:
                    try:
                        mappings = json.loads(content)
                        # Ensure it's a list
                        if not isinstance(mappings, list):
                            mappings = []
                    except json.JSONDecodeError:
                        # Handle malformed JSON
                        mappings = []
                else:
                    # Handle empty file
                    mappings = []
        else:
            mappings = []
        
        return jsonify({'success': True, 'mappings': mappings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/obs/mappings', methods=['POST'])
@admin_required
def api_obs_mappings_post():
    """Save scene to animation mappings"""
    try:
        data = request.get_json()
        
        if not data or 'mappings' not in data:
            return jsonify({'success': False, 'error': 'No mappings data provided'}), 400
        
        mappings = data['mappings']
        
        # Validate mappings structure
        for mapping in mappings:
            if not isinstance(mapping, dict) or 'sceneName' not in mapping or 'animation' not in mapping:
                return jsonify({'success': False, 'error': 'Invalid mapping structure'}), 400
        
        # Ensure config directory exists
        config_dir = DATA_DIR / 'config'
        config_dir.mkdir(exist_ok=True)
        
        # Save mappings
        mappings_path = config_dir / 'obs_mappings.json'
        with open(mappings_path, 'w') as f:
            json.dump(mappings, f, indent=2)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/obs/test-connection', methods=['POST'])
@admin_required
def api_obs_test_connection():
    """Test OBS WebSocket connection"""
    print("=== OBS Connection Test Started ===")
    import time
    start_time = time.time()
    
    try:
        print("Creating temporary OBS client for testing...")
        test_client = OBSWebSocketClient()
        
        # Load and log settings (without password)
        if test_client.load_settings():
            settings_log = test_client.settings.copy()
            if 'password' in settings_log and settings_log['password']:
                settings_log['password'] = '[REDACTED]'
            else:
                settings_log['password'] = '[EMPTY]'
            print(f"Loaded settings: {settings_log}")
        else:
            print("❌ No OBS settings found!")
            return jsonify({'success': False, 'error': 'No OBS settings configured'})
        
        print("Calling test_connection()...")
        success, message = test_client.test_connection()
        
        duration = time.time() - start_time
        print(f"Test completed in {duration:.2f} seconds")
        
        if success:
            print(f"✅ Connection successful: {message}")
            return jsonify({'success': True, 'message': message})
        else:
            print(f"❌ Connection failed: {message}")
            return jsonify({'success': False, 'error': message})
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Exception during test after {duration:.2f} seconds: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        print("=== OBS Connection Test Complete ===")


@app.route('/api/obs/connect', methods=['POST'])
@admin_required
def api_obs_connect():
    """Start persistent OBS WebSocket connection"""
    global obs_client
    try:
        if obs_client and obs_client.connected:
            # Ensure persistent connection is enabled
            obs_client.enable_persistent_connection()
            return jsonify({'success': True, 'message': 'Already connected to OBS (persistent connection enabled)'})
        
        # Create new client if none exists
        if not obs_client:
            obs_client = OBSWebSocketClient()
        
        # Enable persistent connection and connect
        obs_client.enable_persistent_connection()
        
        if obs_client.connected:
            return jsonify({'success': True, 'message': 'Connected to OBS WebSocket server with persistent connection'})
        else:
            return jsonify({'success': False, 'error': 'Failed to connect to OBS WebSocket server'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/obs/disconnect', methods=['POST'])
@admin_required
def api_obs_disconnect():
    """Permanently stop OBS WebSocket connection"""
    global obs_client
    try:
        if obs_client:
            obs_client.disconnect(permanent=True)  # Permanent disconnection
            obs_client = None
        
        return jsonify({'success': True, 'message': 'Permanently disconnected from OBS WebSocket server'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/obs/status', methods=['GET'])
@admin_required
def api_obs_status():
    """Get OBS WebSocket connection status"""
    global obs_client
    try:
        print(f"📊 OBS Status Check - obs_client exists: {obs_client is not None}")
        
        # Check if OBS connection is enabled in settings
        obs_config_path = DATA_DIR / 'config' / 'obs_settings.json'
        obs_enabled = True  # Default to enabled
        
        if obs_config_path.exists():
            try:
                with open(obs_config_path, 'r') as f:
                    settings = json.load(f)
                    obs_enabled = settings.get('enabled', True)
                    print(f"📊 OBS Connection enabled in settings: {obs_enabled}")
            except Exception as e:
                print(f"📊 Error reading settings: {e}")
        
        # If connection is disabled, return disconnected status
        if not obs_enabled:
            print("📊 OBS Connection is disabled by user")
            return jsonify({
                'success': True, 
                'connected': False,
                'current_scene': None,
                'scene_list': [],
                'disabled': True
            })
        
        # If obs_client doesn't exist, try to initialize it ONCE
        if obs_client is None:
            print("🔧 obs_client is None, attempting to initialize...")
            try:
                obs_client = OBSWebSocketClient()
                print("✅ OBS client created successfully")
                
                # Check for settings and enable persistent connection
                if obs_client.load_settings():
                    print("📋 Settings loaded, enabling persistent connection...")
                    obs_client.enable_persistent_connection()
                    print(f"📋 Persistent connection enabled. Connected: {obs_client.connected}")
                else:
                    print("⚠️ No OBS settings found")
            except Exception as init_error:
                print(f"❌ Failed to initialize obs_client: {init_error}")
                obs_client = None
        elif obs_client and not obs_client.should_be_connected and obs_enabled:
            # If we have a client but it's not set to be connected, but settings say it should be
            print("🔧 Re-enabling persistent connection for existing client...")
            obs_client.enable_persistent_connection()
        
        if obs_client:
            print(f"📊 OBS Status - connected: {obs_client.connected}, should_be_connected: {obs_client.should_be_connected}")
        
        if obs_client and obs_client.connected:
            # Verify connection is actually working by trying to get data
            try:
                print(f"📊 Testing connection health by requesting scene data...")
                current_scene = obs_client.get_current_scene()
                scene_list = obs_client.get_scene_list()
                
                print(f"📊 Connection test successful - Current scene: {current_scene}, Scene count: {len(scene_list) if scene_list else 0}")
                
                # Save current scene to persistent storage if we have data
                if current_scene:
                    try:
                        obs_client._save_current_scene_to_storage(current_scene)
                        print(f"💾 Updated persistent storage with current scene: {current_scene}")
                    except Exception as storage_error:
                        print(f"⚠️ Failed to update storage in status check: {storage_error}")
                
                # Note: Scene list is only updated manually via UI refresh button
                # We don't need automatic scene list updates in the backend
                
                # If we got here, connection is working
                return jsonify({
                    'success': True, 
                    'connected': True,
                    'current_scene': current_scene,
                    'scene_list': scene_list  # Still return it for immediate UI display
                })
            except Exception as e:
                print(f"📊 OBS Status - Connection test failed: {e}")
                # Connection is broken, update the client status
                obs_client.connected = False
                
                # Determine if this is a connection timeout vs other error
                error_str = str(e)
                if "10060" in error_str or "timeout" in error_str.lower() or "connection" in error_str.lower():
                    error_message = "Connection failed: Please verify your connection details"
                else:
                    error_message = f"Connection error: {str(e)}"
                
                return jsonify({
                    'success': True, 
                    'connected': False,
                    'current_scene': None,
                    'scene_list': [],
                    'error': error_message
                })
        else:
            return jsonify({
                'success': True, 
                'connected': False,
                'current_scene': None,
                'scene_list': []
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/obs/scenes', methods=['GET'])
@admin_required
def api_obs_scenes():
    """Get list of all OBS scenes - TRANSIENT DATA for UI only"""
    global obs_client
    try:
        if obs_client and obs_client.connected:
            scene_list = obs_client.get_scene_list()
            print(f"📋 Fetched scene list for UI: {len(scene_list) if scene_list else 0} scenes")
            return jsonify({'success': True, 'scenes': scene_list})
        else:
            return jsonify({'success': False, 'error': 'Not connected to OBS'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/obs/current-scene', methods=['GET'])
@admin_required
def api_obs_current_scene_get():
    """Get current scene data from persistent storage"""
    try:
        current_scene_path = DATA_DIR / 'config' / 'obs_current_scene.json'
        
        if current_scene_path.exists():
            with open(current_scene_path, 'r') as f:
                scene_data = json.load(f)
        else:
            # Default data if file doesn't exist
            scene_data = {
                'current_scene': None,
                'last_updated': None,
                'scene_list': []
            }
        
        return jsonify({'success': True, 'scene_data': scene_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/obs/current-scene', methods=['POST'])
@admin_required
def api_obs_current_scene_post():
    """Update current scene data in persistent storage"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Load existing data (minimal structure - no scene_list)
        current_scene_path = DATA_DIR / 'config' / 'obs_current_scene.json'
        if current_scene_path.exists():
            with open(current_scene_path, 'r') as f:
                loaded_data = json.load(f)
                # Only preserve current_scene and last_updated, ignore scene_list
                scene_data = {
                    'current_scene': loaded_data.get('current_scene'),
                    'last_updated': loaded_data.get('last_updated')
                }
        else:
            scene_data = {
                'current_scene': None,
                'last_updated': None
            }
        
        # Update with new data (current_scene only - ignore scene_list)
        if 'current_scene' in data:
            scene_data['current_scene'] = data['current_scene']
            scene_data['last_updated'] = datetime.now().isoformat()
        
        # Note: We intentionally ignore scene_list updates - not stored permanently
        

        
        # Ensure config directory exists
        config_dir = DATA_DIR / 'config'
        config_dir.mkdir(exist_ok=True)
        
        # Save updated data
        with open(current_scene_path, 'w') as f:
            json.dump(scene_data, f, indent=2)
        
        return jsonify({'success': True, 'scene_data': scene_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# Main Application Startup
# =============================================================================

if __name__ == '__main__':
    # Create required directories
    ANIMATIONS_DIR.mkdir(exist_ok=True)
    VIDEOS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    THUMBNAILS_DIR.mkdir(exist_ok=True)
    CONFIG_DIR.mkdir(exist_ok=True)
    
    # Initialize state file with current scene tracking
    ensure_state_file()
    
    # Create default admin user if users.json doesn't exist
    if not USERS_FILE.exists():
        print("Creating default admin user configuration...")
        
        # Generate secure random passwords for default users
        import secrets
        admin_password = secrets.token_urlsafe(12)  # Strong random password
        viewer_password = secrets.token_urlsafe(8)   # Simpler random password
        
        default_users = {
            "admin": {
                "password": admin_password,
                "role": "admin",
                "created": datetime.now().isoformat(),
                "last_login": None
            },
            "viewer": {
                "password": viewer_password,
                "role": "viewer", 
                "created": datetime.now().isoformat(),
                "last_login": None
            },
            "config": {
                "password_requirements": {
                    "min_length": 6,
                    "require_numbers": False,
                    "require_symbols": False
                }
            },
            "session_config": {
                "timeout_minutes": 60,
                "remember_me_days": 7
            }
        }
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_users, f, indent=2)
    
    # Run the Flask-SocketIO server on all interfaces (0.0.0.0) port 8080
    print("OBS-TV-Animator WebSocket Server Starting...")
    print("=" * 84)
    print(f"Available animations: {get_animation_files()}")
    print(f"Available videos: {get_video_files()}")
    print("=" * 84)
    print("🌐 HTTP API Routes:")
    print("  GET  /               - Smart TV display (main animation endpoint)")
    print("  GET  /admin          - Admin dashboard and file management")
    print("  POST /trigger        - Update media via API (JSON: {\"animation\": \"file.html|mp4\"})")
    print("  GET  /animations     - List available media files")
    print("  GET  /health         - Health check endpoint")
    print("=" * 84)
    print("🔌 WebSocket Integration:")
    print(f"  Socket.IO (port {MAIN_PORT}) - Real-time communication")
    print("    • Admin dashboard updates")
    print("    • Animation page refresh & status")
    print("    • OTA Integration (/static/js/ota-integration.js)")
    print(f"  Raw WebSocket (port {WEBSOCKET_PORT}) - StreamerBot compatibility")
    print("    • Legacy integration support")
    print("=" * 84)
    print("📁 Media Storage:")
    print(f"  Animations: {ANIMATIONS_DIR} ({len(get_animation_files())} files)")
    print(f"  Videos: {VIDEOS_DIR} ({len(get_video_files())} files)")
    print(f"  Data: {DATA_DIR} (users, settings, thumbnails)")
    print("=" * 84)
    print("🤖 StreamerBot Integration:")
    print("  • Use 'StreamerBot C#' buttons in admin file management")
    print("  • Copy ready-to-use C# code for each animation")
    print("  • HTTP triggers also available for legacy setups")
    print("  • Visit /admin/instructions/streamerbot-integration for setup guide")
    print("=" * 84)
    print("✨ Custom Animation Development:")
    print("  • Add OTA Integration to your HTML files:")
    print("    <link rel=\"stylesheet\" href=\"/static/css/ota-integration.css\">")
    print("    <script src=\"/static/js/ota-integration.js\"></script>")
    print("  • Enables status indicators, WebSocket sync, and page refresh")
    print("  • Visit /admin/instructions/getting-started for complete guide")
    print("=" * 84)

    try:
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
        obs_scene_watcher = OBSSceneWatcher(str(obs_scene_file), str(obs_mappings_file))
        obs_scene_watcher.start_watching()
        print("✓ OBS Scene Watcher started")
        
        # Start the raw WebSocket server for StreamerBot
        print(f"🚀 Starting Raw WebSocket server on port {WEBSOCKET_PORT} for StreamerBot...")
        try:
            websocket_thread = raw_websocket_server.start_server()
            print("✓ Raw WebSocket server started successfully")
        except Exception as e:
            print(f"❌ Error starting Raw WebSocket server: {e}")
            print("⚠️  Continuing without Raw WebSocket server...")
        
        # Give the WebSocket server a moment to start
        import time
        time.sleep(1)
        print("✓ Raw WebSocket server ready!")
        
        # Initialize OBS WebSocket client (will attempt connection if settings exist)
        print("🎬 Initializing OBS WebSocket client...")
        obs_client = OBSWebSocketClient()
        print("✓ OBS WebSocket client initialized")
        
        # Attempt auto-connection if settings exist
        print("📋 Checking for existing OBS settings...")
        if obs_client.load_settings():
            # Log the loaded settings for debugging (without password)
            settings_debug = obs_client.settings.copy()
            if 'password' in settings_debug:
                settings_debug['password'] = '[REDACTED]' if settings_debug['password'] else '[EMPTY]'
            print(f"📋 Found OBS settings: {settings_debug}")
            
            print("📋 FORCING PERSISTENT OBS CONNECTION...")
            try:
                # CRITICAL: Enable all persistent connection flags FIRST
                obs_client.auto_reconnect_enabled = True
                obs_client.should_be_connected = True
                print("🔧 Persistent connection flags set: auto_reconnect=True, should_be_connected=True")
                
                # Force enable persistent connection (this includes connection attempt)
                obs_client.enable_persistent_connection()
                
                if obs_client.connected:
                    print("✅ SUCCESSFULLY CONNECTED TO OBS - PERSISTENT CONNECTION ACTIVE")
                    print(f"✅ Connection monitoring active: {obs_client.auto_reconnect_enabled}")
                else:
                    print("⚠️  Initial connection failed but PERSISTENT RECONNECTION IS ACTIVE")
                    print("🔄 Connection monitor will continuously attempt reconnection...")
                    
            except Exception as e:
                print(f"❌ CRITICAL: OBS connection error during startup: {e}")
                print("� FORCING RECONNECTION MONITOR ANYWAY...")
                # CRITICAL: Always ensure the monitor is running if settings are enabled
                try:
                    obs_client.auto_reconnect_enabled = True
                    obs_client.should_be_connected = True
                    obs_client._start_connection_monitor()
                    print("✅ FORCED connection monitor started - will reconnect when OBS available")
                except Exception as monitor_error:
                    print(f"❌ FATAL: Could not start connection monitor: {monitor_error}")
        else:
            print("ℹ️  No OBS settings found - connection will be available when configured")
        
        print("🚀 Starting Flask-SocketIO server...")
        socketio.run(app, host='0.0.0.0', port=MAIN_PORT, debug=False, allow_unsafe_werkzeug=True)
        
    except Exception as e:
        print(f"❌ FATAL ERROR during startup: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️  Server startup failed!")
