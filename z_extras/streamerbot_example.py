#!/usr/bin/env python3
"""
StreamerBot WebSocket Integration Example for OBS-TV-Animator
This script demonstrates how to integrate with StreamerBot for advanced automation.
"""

import socketio
import json
import time
import sys
from datetime import datetime


class StreamerBotConnector:
    """WebSocket connector for StreamerBot integration with OBS-TV-Animator"""
    
    def __init__(self, server_url="http://localhost:8080"):
        self.server_url = server_url
        self.sio = socketio.Client()
        self.connected = False
        
        # Setup event handlers
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('animation_changed', self._on_animation_changed)
        self.sio.on('status', self._on_status)
        self.sio.on('error', self._on_error)
        self.sio.on('info', self._on_info)
    
    def _on_connect(self):
        """Handle connection to OBS-TV-Animator server"""
        self.connected = True
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to OBS-TV-Animator server")
    
    def _on_disconnect(self):
        """Handle disconnection from server"""
        self.connected = False
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Disconnected from server")
    
    def _on_animation_changed(self, data):
        """Handle animation change notifications"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Animation changed: {data.get('message')}")
        
    def _on_status(self, data):
        """Handle status updates"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {json.dumps(data, indent=2)}")
    
    def _on_error(self, data):
        """Handle error messages"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {data.get('message')}")
    
    def _on_info(self, data):
        """Handle info messages"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: {data.get('message')}")
    
    def connect(self):
        """Connect to the OBS-TV-Animator server"""
        try:
            self.sio.connect(self.server_url)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            self.sio.disconnect()
    
    def trigger_animation(self, animation_name):
        """Trigger a specific animation"""
        if not self.connected:
            return False
        
        self.sio.emit('trigger_animation', {'animation': animation_name})
        return True
    
    def handle_scene_change(self, scene_name, custom_mapping=None):
        """Handle OBS scene change event"""
        if not self.connected:
            return False
        
        payload = {'scene_name': scene_name}
        if custom_mapping:
            payload['animation_mapping'] = custom_mapping
        
        self.sio.emit('scene_change', payload)
        return True
    
    def send_streamerbot_event(self, event_type, data):
        """Send StreamerBot event to server"""
        if not self.connected:
            return False
        
        self.sio.emit('streamerbot_event', {
            'event_type': event_type,
            'data': data
        })
        return True
    
    def get_status(self):
        """Request current server status"""
        if not self.connected:
            return False
        
        self.sio.emit('get_status')
        return True


def demo_streamerbot_integration():
    """Demonstrate StreamerBot integration scenarios"""
    
    connector = StreamerBotConnector()
    
    if not connector.connect():
        print("Failed to connect to OBS-TV-Animator server")
        return
    
    try:
        # Wait for connection to establish
        time.sleep(1)
        
        print("\n=== StreamerBot Integration Demo ===")
        
        # 1. Scene change simulation
        print("\n1. Simulating OBS scene changes...")
        connector.handle_scene_change("Gaming")
        time.sleep(2)
        
        connector.handle_scene_change("Chatting")  
        time.sleep(2)
        
        # 2. Custom event simulation
        print("\n2. Simulating StreamerBot custom events...")
        
        # Follower alert
        connector.send_streamerbot_event("trigger_animation", {
            "animation": "anim1.html"
        })
        time.sleep(2)
        
        # Donation alert
        connector.send_streamerbot_event("custom_animation", {
            "animation": "anim2.html"
        })
        time.sleep(2)
        
        # 3. Custom scene mapping
        print("\n3. Testing custom scene mapping...")
        custom_mapping = {
            "special_scene": "anim3.html",
            "gaming": "anim1.html"
        }
        
        connector.handle_scene_change("special_scene", custom_mapping)
        time.sleep(2)
        
        # 4. Status check
        print("\n4. Getting server status...")
        connector.get_status()
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    finally:
        connector.disconnect()
        print("Demo completed")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_streamerbot_integration()
    else:
        print("StreamerBot Connector for OBS-TV-Animator")
        print("\nUsage:")
        print("  python streamerbot_example.py demo    - Run integration demo")
        print("\nFor StreamerBot integration:")
        print("1. Import this module: from streamerbot_example import StreamerBotConnector")
        print("2. Create connector: connector = StreamerBotConnector('http://your-server:8080')")
        print("3. Connect: connector.connect()")
        print("4. Send events: connector.send_streamerbot_event('event_type', data)")
        print("\nExample StreamerBot Actions:")
        print("- New Follower: connector.trigger_animation('follower_alert.html')")
        print("- Scene Change: connector.handle_scene_change('%sceneName%')")
        print("- Donation Alert: connector.send_streamerbot_event('custom_animation', {'animation': 'donation.html'})")