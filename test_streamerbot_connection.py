#!/usr/bin/env python3
"""
Test script to simulate StreamerBot WebSocket connection
This script connects to the raw WebSocket server to test the connection status display
"""

import asyncio
import websockets
import json
import time

async def test_streamerbot_connection():
    """Test StreamerBot WebSocket connection"""
    uri = "ws://localhost:8081"
    
    try:
        print("Connecting to StreamerBot WebSocket server...")
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to StreamerBot WebSocket server!")
            print("Check the admin dashboard - StreamerBot should show as 'Connected'")
            
            # Send a status request
            status_request = {
                "action": "get_status"
            }
            await websocket.send(json.dumps(status_request))
            print(f"Sent status request: {status_request}")
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received response: {response}")
            
            # Keep connection alive for testing
            print("\nKeeping connection alive for 30 seconds...")
            print("Check the admin dashboard to see StreamerBot connection status!")
            await asyncio.sleep(30)
            
            # Test animation trigger
            print("\nTesting animation trigger...")
            trigger_request = {
                "action": "trigger_animation",
                "animation": "anim1.html",
                "instant": True,
                "force_refresh": True
            }
            await websocket.send(json.dumps(trigger_request))
            print(f"Sent trigger request: {trigger_request}")
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received response: {response}")
            
            print("\nConnection test complete!")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_streamerbot_connection())