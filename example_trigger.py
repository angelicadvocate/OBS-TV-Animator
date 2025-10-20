#!/usr/bin/env python3
"""
Example script to trigger animation changes from OBS or other automation tools.
This demonstrates how to programmatically switch animations.
"""

import requests
import sys
import json


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


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python example_trigger.py [list|trigger] [animation_name]")
        print("\nExamples:")
        print("  python example_trigger.py list")
        print("  python example_trigger.py trigger anim2.html")
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
    
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: list, trigger")
        sys.exit(1)
