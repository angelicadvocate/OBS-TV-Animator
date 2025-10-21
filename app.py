#!/usr/bin/env python3
"""
OBS-TV-Animator: A Flask-SocketIO server to display HTML/CSS/JS animations on a Smart TV.
Supports dynamic updates triggered via OBS WebSocket, StreamerBot, or REST API.
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

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
ANIMATIONS_DIR = Path(__file__).parent / "animations"
VIDEOS_DIR = Path(__file__).parent / "videos"
DATA_DIR = Path(__file__).parent / "data"
CONFIG_DIR = DATA_DIR / "config"  # Config now under data directory
LOGS_DIR = DATA_DIR / "logs"      # Logs now under data directory
STATE_FILE = DATA_DIR / "state.json"
USERS_FILE = CONFIG_DIR / "users.json"

# Supported file extensions
HTML_EXTENSIONS = {'.html', '.htm'}
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.ogg', '.avi', '.mov', '.mkv'}

# Connected devices tracking
connected_devices = {}  # {session_id: {'type': 'tv'|'admin', 'user_agent': str, 'connected_at': timestamp}}
admin_sessions = set()  # Track admin dashboard sessions

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


def get_connected_devices_info():
    """Get information about connected devices"""
    tv_devices = []
    admin_count = 0
    
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
    
    return {
        'tv_devices': tv_devices,
        'tv_count': len(tv_devices),
        'admin_count': admin_count,
        'total_count': len(connected_devices)
    }


def get_tv_devices_count():
    """Get count of connected TV devices (excluding admin)"""
    return len([d for d in connected_devices.values() if d['type'] == 'tv'])


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

        # Emit explicit page refresh
        socketio.emit('page_refresh', {
            'reason': 'media_changed',
            'new_media': media_file,
            'media_type': media_type
        })

        return jsonify({
            "success": True,
            "current_animation": media_file,
            "media_type": media_type,
            "message": f"Media updated to '{media_file}' ({media_type})"
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
                         show_credentials_warning=show_credentials_warning)


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
                         current_username=current_user.username)


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
                         current_username=current_user.username)


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
@admin_required
def admin_status():
    """API endpoint for admin dashboard status"""
    try:
        state = load_state()
        current_media = state.get('current_animation')
        media_path, media_type = find_media_file(current_media) if current_media else (None, None)
        
        # Get device information
        devices_info = get_connected_devices_info()
        
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
            'total_connections': devices_info['total_count'],
            'available_animations': get_animation_files(),
            'available_videos': get_video_files(),
            'available_media': get_all_media_files()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/files')
@admin_required
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
        # For HTML files, return a simple SVG placeholder
        if filename.endswith('.html'):
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="150" fill="#2c3e50"/>
  <text x="100" y="80" text-anchor="middle" fill="white" font-family="Arial" font-size="14">{filename}</text>
  <text x="100" y="100" text-anchor="middle" fill="#bdc3c7" font-family="Arial" font-size="10">HTML Animation</text>
</svg>'''
            return svg_content, 200, {'Content-Type': 'image/svg+xml'}
        
        # For video files, return a video placeholder
        else:
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="150" fill="#34495e"/>
  <polygon points="80,60 80,90 110,75" fill="white"/>
  <text x="100" y="110" text-anchor="middle" fill="white" font-family="Arial" font-size="12">{filename}</text>
  <text x="100" y="125" text-anchor="middle" fill="#bdc3c7" font-family="Arial" font-size="9">Video File</text>
</svg>'''
            return svg_content, 200, {'Content-Type': 'image/svg+xml'}
        
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
    print("HTTP API Routes:")
    print("  GET  /               - View current media on TV")
    print("  POST /trigger        - Update media (JSON: {\"animation\": \"file.html|mp4\"})")
    print("  GET  /animations     - List available media files")
    print("  GET  /videos/<file>  - Serve video files")
    print("  GET  /health         - Health check")
    print("=" * 84)
    print("WebSocket Events (for OBS/StreamerBot):")
    print("  trigger_animation - Change media: {\"animation\": \"file.html|mp4\"}")
    print("  scene_change      - OBS scene change: {\"scene_name\": \"Gaming\"}")
    print("  streamerbot_event - StreamerBot events")
    print("  video_control     - Video controls: {\"action\": \"play|pause|seek\", \"value\": 0}")
    print("  get_status        - Get current status")
    print("=" * 84)
    print("Media Directories:")
    print(f"  Animations: {ANIMATIONS_DIR}")
    print(f"  Videos: {VIDEOS_DIR}")
    print("=" * 84)
    
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)
