#!/usr/bin/env python3
"""
OBS-TV-Animator: A Flask server to display HTML/CSS/JS animations on a Smart TV.
Supports dynamic updates triggered via OBS or webhooks.
"""

import json
import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__)

# Configuration
ANIMATIONS_DIR = Path(__file__).parent / "animations"
DATA_DIR = Path(__file__).parent / "data"
STATE_FILE = DATA_DIR / "state.json"


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


@app.route('/')
def index():
    """Serve the current animation"""
    state = load_state()
    current_animation = state.get('current_animation', 'anim1.html')
    
    # Check if animation file exists
    animation_path = ANIMATIONS_DIR / current_animation
    if not animation_path.exists():
        # Fallback to first available animation or show error
        animations = get_animation_files()
        if animations:
            current_animation = animations[0]
            state['current_animation'] = current_animation
            save_state(state)
        else:
            return "No animations available. Please add HTML files to the animations/ directory.", 404
    
    return send_from_directory(ANIMATIONS_DIR, current_animation)


@app.route('/trigger', methods=['POST'])
def trigger():
    """Update the current animation via JSON payload"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400
        
        animation = data.get('animation')
        if not animation:
            return jsonify({"error": "Missing 'animation' field in payload"}), 400
        
        # Validate that the animation file exists
        animation_path = ANIMATIONS_DIR / animation
        if not animation_path.exists():
            available_animations = get_animation_files()
            return jsonify({
                "error": f"Animation '{animation}' not found",
                "available_animations": available_animations
            }), 404
        
        # Update state
        state = load_state()
        state['current_animation'] = animation
        save_state(state)
        
        return jsonify({
            "success": True,
            "current_animation": animation,
            "message": f"Animation updated to '{animation}'"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/animations', methods=['GET'])
def list_animations():
    """List all available animation files"""
    animations = get_animation_files()
    state = load_state()
    current_animation = state.get('current_animation', None)
    
    return jsonify({
        "animations": animations,
        "current_animation": current_animation,
        "count": len(animations)
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "animations_available": len(get_animation_files())
    }), 200


if __name__ == '__main__':
    # Ensure required directories exist
    ANIMATIONS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    
    # Initialize state file if it doesn't exist
    if not STATE_FILE.exists():
        save_state({"current_animation": "anim1.html"})
    
    # Run the Flask app on all interfaces (0.0.0.0) port 8080
    print("=" * 60)
    print("OBS-TV-Animator Server Starting...")
    print("=" * 60)
    print(f"Available animations: {get_animation_files()}")
    print(f"Current animation: {load_state().get('current_animation')}")
    print("=" * 60)
    print("Server running at http://0.0.0.0:8080")
    print("Routes:")
    print("  GET  /            - View current animation")
    print("  POST /trigger     - Update animation (JSON: {\"animation\": \"filename.html\"})")
    print("  GET  /animations  - List available animations")
    print("  GET  /health      - Health check")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8080, debug=False)
