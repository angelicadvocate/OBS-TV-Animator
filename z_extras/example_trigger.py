#!/usr/bin/env python3
"""
Example script to trigger animation changes from OBS or other automation tools.
This demonstrates how to programmatically switch animations via HTTP API or WebSocket.
"""

import requests
import sys
import json
import socketio
import time


def trigger_animation(animation_name, server_url="http://localhost:8080"):
    """
    Trigger a specific animation on the server.
    
    Args:
        animation_name: Name of the animation file (e.g., 'anim1.html')
        server_url: Base URL of the OBS-TV-Animator server
    
    Returns:
        dict: Response from the server
    """
    url = f"{server_url}/trigger"
    payload = {"animation": animation_name}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def list_animations(server_url="http://localhost:8080"):
    """
    Get list of available animations from the server.
    
    Args:
        server_url: Base URL of the OBS-TV-Animator server
    
    Returns:
        dict: Response with list of animations
    """
    url = f"{server_url}/animations"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def trigger_animation_websocket(animation_name, server_url="http://localhost:8080"):
    """
    Trigger a specific animation via WebSocket connection.
    
    Args:
        animation_name: Name of the animation file (e.g., 'anim1.html')
        server_url: Base URL of the OBS-TV-Animator server
    
    Returns:
        dict: Response from the server
    """
    try:
        # Create SocketIO client
        sio = socketio.Client()
        result = {"error": "Connection failed"}
        
        @sio.event
        def connect():
            print(f"Connected to WebSocket server: {server_url}")
        
        @sio.event
        def disconnect():
            print("Disconnected from WebSocket server")
        
        @sio.event
        def animation_changed(data):
            nonlocal result
            result = {
                "success": True,
                "message": data.get('message', 'Animation changed successfully'),
                "current_animation": data.get('current_animation'),
                "previous_animation": data.get('previous_animation')
            }
        
        @sio.event
        def error(data):
            nonlocal result
            result = {"error": data.get('message', 'Unknown error')}
        
        # Connect and send animation trigger
        sio.connect(server_url)
        sio.emit('trigger_animation', {'animation': animation_name})
        
        # Wait for response
        time.sleep(1)
        sio.disconnect()
        
        return result
        
    except Exception as e:
        return {"error": f"WebSocket error: {str(e)}"}


def trigger_scene_change_websocket(scene_name, server_url="http://localhost:8080", animation_mapping=None):
    """
    Trigger scene change via WebSocket (for OBS integration).
    
    Args:
        scene_name: Name of the OBS scene
        server_url: Base URL of the OBS-TV-Animator server
        animation_mapping: Optional dict mapping scene names to animations
    
    Returns:
        dict: Response from the server
    """
    try:
        sio = socketio.Client()
        result = {"error": "Connection failed"}
        
        @sio.event
        def connect():
            print(f"Connected to WebSocket server: {server_url}")
        
        @sio.event
        def disconnect():
            print("Disconnected from WebSocket server")
        
        @sio.event
        def animation_changed(data):
            nonlocal result
            result = {
                "success": True,
                "message": data.get('message', 'Scene change processed'),
                "current_animation": data.get('current_animation'),
                "scene_name": scene_name
            }
        
        @sio.event
        def info(data):
            nonlocal result
            result = {"info": data.get('message', 'Scene change info')}
        
        @sio.event
        def error(data):
            nonlocal result
            result = {"error": data.get('message', 'Unknown error')}
        
        # Connect and send scene change
        sio.connect(server_url)
        
        payload = {"scene_name": scene_name}
        if animation_mapping:
            payload["animation_mapping"] = animation_mapping
            
        sio.emit('scene_change', payload)
        
        # Wait for response
        time.sleep(1)
        sio.disconnect()
        
        return result
        
    except Exception as e:
        return {"error": f"WebSocket error: {str(e)}"}


def control_video_websocket(action, value=None, server_url="http://localhost:8080"):
    """
    Control video playback via WebSocket.
    
    Args:
        action: Video control action (play, pause, seek, volume, etc.)
        value: Optional value for actions that need it (seek time, volume level)
        server_url: Base URL of the OBS-TV-Animator server
    
    Returns:
        dict: Response from the server
    """
    try:
        sio = socketio.Client()
        result = {"error": "Connection failed"}
        
        @sio.event
        def connect():
            print(f"Connected to WebSocket server: {server_url}")
        
        @sio.event
        def disconnect():
            print("Disconnected from WebSocket server")
        
        @sio.event
        def video_control(data):
            nonlocal result
            result = {
                "success": True,
                "action": data.get('action'),
                "value": data.get('value'),
                "message": data.get('message', 'Video control executed')
            }
        
        @sio.event
        def error(data):
            nonlocal result
            result = {"error": data.get('message', 'Unknown error')}
        
        # Connect and send video control
        sio.connect(server_url)
        
        payload = {"action": action}
        if value is not None:
            payload["value"] = value
            
        sio.emit('video_control', payload)
        
        # Wait for response
        time.sleep(1)
        sio.disconnect()
        
        return result
        
    except Exception as e:
        return {"error": f"WebSocket error: {str(e)}"}


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python example_trigger.py [command] [arguments...]")
        print("\nCommands:")
        print("  list                          - List available media files")
        print("  trigger <media>               - Trigger media via HTTP API")
        print("  websocket <media>             - Trigger media via WebSocket")
        print("  scene <scene_name>            - Trigger scene change via WebSocket")
        print("  video <action> [value]        - Control video playback")
        print("\nExamples:")
        print("  python example_trigger.py list")
        print("  python example_trigger.py trigger anim2.html")
        print("  python example_trigger.py trigger video1.mp4")
        print("  python example_trigger.py websocket my_video.mp4")
        print("  python example_trigger.py scene Gaming")
        print("  python example_trigger.py video pause")
        print("  python example_trigger.py video seek 30")
        print("  python example_trigger.py video volume 0.8")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        result = list_animations()
        print(json.dumps(result, indent=2))
    
    elif command == "trigger":
        if len(sys.argv) < 3:
            print("Error: Please specify animation name")
            print("Example: python example_trigger.py trigger anim2.html")
            sys.exit(1)
        
        animation_name = sys.argv[2]
        result = trigger_animation(animation_name)
        print(json.dumps(result, indent=2))
    
    elif command == "websocket":
        if len(sys.argv) < 3:
            print("Error: Please specify animation name")
            print("Example: python example_trigger.py websocket anim2.html")
            sys.exit(1)
        
        animation_name = sys.argv[2]
        result = trigger_animation_websocket(animation_name)
        print(json.dumps(result, indent=2))
    
    elif command == "scene":
        if len(sys.argv) < 3:
            print("Error: Please specify scene name")
            print("Example: python example_trigger.py scene Gaming")
            sys.exit(1)
        
        scene_name = sys.argv[2]
        
        # Default scene-to-animation mapping
        default_mapping = {
            "gaming": "anim1.html",
            "chatting": "anim2.html", 
            "brb": "anim3.html",
            "be right back": "anim3.html"
        }
        
        result = trigger_scene_change_websocket(scene_name, animation_mapping=default_mapping)
        print(json.dumps(result, indent=2))
    
    elif command == "video":
        if len(sys.argv) < 3:
            print("Error: Please specify video action")
            print("Examples:")
            print("  python example_trigger.py video play")
            print("  python example_trigger.py video pause") 
            print("  python example_trigger.py video toggle")
            print("  python example_trigger.py video seek 30")
            print("  python example_trigger.py video volume 0.8")
            print("  python example_trigger.py video mute true")
            print("  python example_trigger.py video restart")
            sys.exit(1)
        
        action = sys.argv[2]
        value = sys.argv[3] if len(sys.argv) > 3 else None
        
        # Convert value to appropriate type
        if value is not None:
            if action in ["seek", "volume"]:
                try:
                    value = float(value)
                except ValueError:
                    print(f"Error: {action} requires a numeric value")
                    sys.exit(1)
            elif action == "mute":
                value = value.lower() in ["true", "1", "yes", "on"]
        
        result = control_video_websocket(action, value)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: list, trigger, websocket, scene, video")
        sys.exit(1)
