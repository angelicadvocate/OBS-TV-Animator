# StreamerBot WebSocket Integration Research

## Investigation Status
- ✅ Confirmed existing WebSocket infrastructure in OBS-TV-Animator
- ✅ Configured StreamerBot custom WebSocket server (127.0.0.1:8080, endpoint: /socket.io/)
- ✅ **SOLUTION FOUND**: StreamerBot has built-in C# methods for WebSocket communication!
- ✅ Identified `CPH.WebsocketSend()` method for sending to custom WebSocket clients

## StreamerBot WebSocket Methods

### Method 1: WebSocket Client Sub-Action
StreamerBot has WebSocket client capabilities in newer versions:
1. **Add Sub-Action**: Core → Network → WebSocket Client
2. **Connect to**: ws://localhost:8080 (our SocketIO server)
3. **Send JSON**: {"event_type": "trigger_animation", "data": {"animation": "anim2.html"}}

### Method 2: Custom C# WebSocket Client
If WebSocket Client sub-action isn't available, we can use C# with System.Net.WebSockets:
```csharp
using System;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

public class CPHInline
{
    public async Task<bool> Execute()
    {
        try
        {
            using (var client = new ClientWebSocket())
            {
                var uri = new Uri("ws://localhost:8080/socket.io/?EIO=4&transport=websocket");
                await client.ConnectAsync(uri, CancellationToken.None);
                
                var message = "42[\"streamerbot_event\",{\"event_type\":\"trigger_animation\",\"data\":{\"animation\":\"anim2.html\"}}]";
                var buffer = Encoding.UTF8.GetBytes(message);
                
                await client.SendAsync(new ArraySegment<byte>(buffer), WebSocketMessageType.Text, true, CancellationToken.None);
                
                // Wait for response
                var responseBuffer = new byte[1024];
                var result = await client.ReceiveAsync(new ArraySegment<byte>(responseBuffer), CancellationToken.None);
                var response = Encoding.UTF8.GetString(responseBuffer, 0, result.Count);
                
                CPH.LogInfo($"WebSocket response: {response}");
                
                return true;
            }
        }
        catch (Exception ex)
        {
            CPH.LogError($"WebSocket error: {ex.Message}");
            return false;
        }
    }
}
```

### Method 3: StreamerBot WebSocket Server Mode
Some StreamerBot versions can act as WebSocket servers. We could:
1. Configure StreamerBot as WebSocket server
2. Make OBS-TV-Animator connect as client
3. Send confirmations back to StreamerBot

## Benefits of WebSocket vs HTTP
1. ✅ **Bidirectional communication** - Immediate feedback
2. ✅ **Real-time status updates** - Know if animation succeeded/failed
3. ✅ **Lower latency** - Persistent connection
4. ✅ **Better error handling** - Connection status awareness
5. ✅ **Event confirmations** - StreamerBot gets success/failure response

## StreamerBot C# WebSocket Methods (SOLUTION!)

### Available Methods:
1. **`CPH.WebsocketSend(string data, int connection = 0)`**
   - Sends data to a specific WebSocket client
   - `connection` parameter is the index (0-based) of custom WebSocket clients
   - Perfect for sending to our OBS-TV-Animator server!

2. **`CPH.WebsocketBroadcastJson(string data)`**
   - Broadcasts JSON to ALL connected WebSocket clients
   - Use if we want to send to multiple servers

### Usage Example:
```csharp
using System;
public class CPHInline
{
    public bool Execute()
    {
        // Send animation trigger to OBS-TV-Animator
        string json = "{\"event\":\"trigger_animation\",\"animation\":\"anim1\"}";
        CPH.WebsocketSend(json, 0); // Send to first custom WebSocket client (our server)
        return true;
    }
}
```

```

## Testing Results & Next Steps
1. ✅ **FOUND SOLUTION**: Use `CPH.WebsocketSend()` method!
2. ✅ C# action created and executing successfully in StreamerBot
3. ⚠️ **CONNECTION ISSUE**: StreamerBot not connecting to our Socket.IO server
4. 🔍 **CURRENT PROBLEM**: Custom WebSocket client configuration needs adjustment

### StreamerBot Logs Confirm:
```
[2025-10-23 06:54:27.211 INF] Sending WebSocket message: {"event":"trigger_animation","animation":"anim1"}
[2025-10-23 06:54:27.213 INF] WebSocket message sent successfully
```
✅ C# code works perfectly!
❌ But no connection visible on our server = connection configuration issue

### Immediate Steps:
1. Fix StreamerBot custom WebSocket client connection (Socket.IO protocol?)
2. Test actual message delivery to OBS-TV-Animator server
3. Verify bidirectional communication works
4. Document working configuration

## WebSocket Message Format
```json
{
  "event_type": "trigger_animation",
  "data": {
    "animation": "anim2.html",
    "source": "streamerbot",
    "user": "%user%",
    "event": "follow"
  }
}
```

Expected Response:
```json
{
  "status": "success",
  "animation": "anim2.html",
  "message": "Animation triggered successfully",
  "timestamp": "2025-10-23T10:30:00Z"
}
```