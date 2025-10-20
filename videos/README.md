# Videos Directory

This directory contains video files that can be displayed on your Smart TV.

## Supported Video Formats

- **MP4** (.mp4) - Recommended for best compatibility
- **WebM** (.webm) - Good for web browsers  
- **OGG** (.ogg) - Open source format
- **AVI** (.avi) - Legacy format
- **MOV** (.mov) - QuickTime format
- **MKV** (.mkv) - Matroska format

## Adding Video Files

1. Copy your video files into this `videos/` directory
2. Use the `/trigger` API or WebSocket events to switch to them
3. Video files will auto-play, auto-fullscreen, and loop on the TV

## Example Usage

### HTTP API
```bash
curl -X POST http://localhost:8080/trigger \
  -H "Content-Type: application/json" \
  -d '{"animation": "my_video.mp4"}'
```

### WebSocket
```javascript
socket.emit('trigger_animation', {
  animation: 'my_video.mp4'
});
```

### Python Script
```bash
python example_trigger.py trigger my_video.mp4
python example_trigger.py websocket my_video.mp4
```

## Video Controls

When a video is playing, you can control it via WebSocket:

```javascript
// Play/pause
socket.emit('video_control', {action: 'toggle'});

// Seek to specific time (in seconds)
socket.emit('video_control', {action: 'seek', value: 30});

// Set volume (0.0 to 1.0)
socket.emit('video_control', {action: 'volume', value: 0.8});

// Mute/unmute
socket.emit('video_control', {action: 'mute', value: true});

// Restart video
socket.emit('video_control', {action: 'restart'});
```

## Keyboard Controls (on TV)

When a video is displayed on the TV, these keyboard shortcuts work:

- **Space/K** - Play/Pause
- **F** - Toggle fullscreen  
- **M** - Mute/Unmute
- **R** - Restart video
- **←/→** - Seek backward/forward 10 seconds

## Tips

- **File Size**: Keep videos reasonably sized for smooth playback on Smart TV browsers
- **Codecs**: Use H.264 video codec and AAC audio codec for best compatibility
- **Resolution**: 1080p (1920x1080) is recommended for most Smart TVs
- **Duration**: Videos automatically loop, so any length works
- **Performance**: Test video playback on your specific Smart TV model

## StreamerBot Integration

You can trigger videos based on StreamerBot events:

```javascript
// New follower triggers celebration video
socket.emit('streamerbot_event', {
  event_type: 'trigger_animation',
  data: {
    animation: 'celebration.mp4'
  }
});

// Scene change triggers background video
socket.emit('scene_change', {
  scene_name: 'Gaming',
  animation_mapping: {
    'gaming': 'gaming_background.mp4',
    'chatting': 'chat_background.mp4'
  }
});
```