#!/usr/bin/env python3
"""
Test WebSocket Client for StreamerBot Raw WebSocket Server
Tests the raw WebSocket server on port 8081
"""

import asyncio
import websockets
import json

async def test_websocket_connection():
    uri = "ws://127.0.0.1:8081"
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully!")
            
            # Test 1: Send trigger_animation message
            print("\n🎬 Testing animation trigger...")
            trigger_message = {
                "action": "trigger_animation",
                "animation": "anim1.html"
            }
            
            await websocket.send(json.dumps(trigger_message))
            print(f"Sent: {trigger_message}")
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Received: {response_data}")
            
            # Test 2: Send get_status message
            print("\n📊 Testing status request...")
            status_message = {
                "action": "get_status"
            }
            
            await websocket.send(json.dumps(status_message))
            print(f"Sent: {status_message}")
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Received: {response_data}")
            
            # Test 3: Send invalid message
            print("\n❌ Testing invalid message...")
            invalid_message = {
                "action": "invalid_action"
            }
            
            await websocket.send(json.dumps(invalid_message))
            print(f"Sent: {invalid_message}")
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Received: {response_data}")
            
            print("\n✓ All tests completed!")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused. Make sure the server is running on port 8081.")
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("Raw WebSocket Client Test")
    print("=" * 40)
    asyncio.run(test_websocket_connection())