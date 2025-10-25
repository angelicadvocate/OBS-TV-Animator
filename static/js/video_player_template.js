class VideoPlayer {
    constructor() {
        this.video = document.getElementById('mainVideo');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.videoInfo = document.getElementById('videoInfo');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.socket = null;
        this.filename = window.videoFilename || 'Unknown';
        
        this.initVideo();
        this.initWebSocket();
        this.initKeyboardControls();
        this.startHeartbeat();
    }
    
    initVideo() {
        // Video event listeners
        this.video.addEventListener('loadstart', () => {
            console.log('Video loading started');
            this.showLoading(true);
        });
        
        this.video.addEventListener('canplay', () => {
            console.log('Video can start playing');
            this.showLoading(false);
            this.showVideoInfo();
            
            // Attempt to enter fullscreen and play
            this.enterFullscreen();
            this.playVideo();
        });
        
        this.video.addEventListener('ended', () => {
            console.log('Video ended - looping');
            this.playVideo(); // Restart video
        });
        
        this.video.addEventListener('error', (e) => {
            console.error('Video error:', e);
            this.showError('Failed to load video: ' + this.filename);
        });
        
        this.video.addEventListener('play', () => {
            console.log('Video started playing');
            this.showVideoInfo();
        });
        
        this.video.addEventListener('pause', () => {
            console.log('Video paused');
        });
    }
    
    initWebSocket() {
        try {
            const serverUrl = window.location.origin;
            this.socket = io(serverUrl);
            
            // Connection events
            this.socket.on('connect', () => {
                console.log('Connected to OBS-TV-Animator server');
                this.updateStatus('Connected', true);
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
                this.updateStatus('Disconnected', false);
            });
            
            // Media change events
            this.socket.on('animation_changed', (data) => {
                console.log('Media changed:', data);
                this.handleMediaChange(data);
                
                // Auto-refresh page if requested (for seamless media changes)
                if (data.refresh_page) {
                    console.log('Page refresh requested, reloading in 1 second...');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            });
            
            // Listen for explicit page refresh commands
            this.socket.on('page_refresh', (data) => {
                console.log('Page refresh command received:', data);
                this.showRefreshNotification(data);
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            });
            
            // Video control events
            this.socket.on('video_control', (data) => {
                console.log('Video control:', data);
                this.handleVideoControl(data);
            });
            
            this.socket.on('status', (data) => {
                console.log('Server status:', data);
            });
            
            this.socket.on('error', (data) => {
                console.error('Server error:', data);
                this.updateStatus('Error: ' + data.message, false);
            });
            
        } catch (error) {
            console.error('WebSocket initialization failed:', error);
            this.updateStatus('Connection Failed', false);
        }
    }
    
    initKeyboardControls() {
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case ' ':
                case 'k':
                    e.preventDefault();
                    this.togglePlayPause();
                    break;
                case 'f':
                    e.preventDefault();
                    this.toggleFullscreen();
                    break;
                case 'm':
                    e.preventDefault();
                    this.toggleMute();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.seek(-10);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.seek(10);
                    break;
                case 'r':
                    e.preventDefault();
                    this.restartVideo();
                    break;
            }
        });
    }
    
    enterFullscreen() {
        try {
            const container = document.getElementById('videoContainer');
            if (container.requestFullscreen) {
                container.requestFullscreen();
            } else if (container.webkitRequestFullscreen) {
                container.webkitRequestFullscreen();
            } else if (container.msRequestFullscreen) {
                container.msRequestFullscreen();
            }
        } catch (error) {
            console.log('Fullscreen not supported or denied:', error);
        }
    }
    
    playVideo() {
        const playPromise = this.video.play();
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.error('Auto-play failed:', error);
                // Show user interaction required message
                this.showError('Click anywhere to start video (auto-play blocked)');
                document.addEventListener('click', () => {
                    this.video.play();
                }, { once: true });
            });
        }
    }
    
    updateStatus(message, connected) {
        // Update tooltip with message, but no visible text
        this.statusIndicator.title = `OTA: ${message}`;
        this.statusIndicator.className = connected ? 
            'ota-status-indicator connected' : 
            'ota-status-indicator disconnected';
    }
    
    showLoading(show) {
        this.loadingIndicator.style.display = show ? 'block' : 'none';
    }
    
    showVideoInfo() {
        this.videoInfo.classList.add('show');
        setTimeout(() => {
            this.videoInfo.classList.remove('show');
        }, 3000);
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.innerHTML = `<h3>Video Error</h3><p>${message}</p>`;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
    
    handleMediaChange(data) {
        if (data.current_animation) {
            // Reload page if media changed
            console.log('Media changed, reloading...');
            setTimeout(() => {
                window.location.reload();
            }, 500);
        }
    }
    
    showRefreshNotification(data) {
        // Show a brief notification before page refresh
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 20px 40px;
            border-radius: 10px;
            font-size: 18px;
            z-index: 9999;
            text-align: center;
        `;
        notification.innerHTML = `
            <div>Loading new content...</div>
            <div style="font-size: 14px; margin-top: 10px; opacity: 0.8;">
                ${data.new_media} (${data.media_type})
            </div>
        `;
        document.body.appendChild(notification);
        
        // Remove notification after refresh (cleanup)
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 2000);
    }
    
    handleVideoControl(data) {
        const { action, value } = data;
        
        switch(action) {
            case 'play':
                this.video.play();
                break;
            case 'pause':
                this.video.pause();
                break;
            case 'toggle':
                this.togglePlayPause();
                break;
            case 'seek':
                this.video.currentTime = value;
                break;
            case 'volume':
                this.video.volume = Math.max(0, Math.min(1, value));
                break;
            case 'mute':
                this.video.muted = value;
                break;
            case 'restart':
                this.restartVideo();
                break;
        }
    }
    
    togglePlayPause() {
        if (this.video.paused) {
            this.video.play();
        } else {
            this.video.pause();
        }
    }
    
    toggleFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            this.enterFullscreen();
        }
    }
    
    toggleMute() {
        this.video.muted = !this.video.muted;
    }
    
    seek(seconds) {
        this.video.currentTime += seconds;
    }
    
    restartVideo() {
        this.video.currentTime = 0;
        this.video.play();
    }
    
    startHeartbeat() {
        // Request status every 30 seconds
        setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('get_status');
            }
        }, 30000);
    }
}

// Initialize video player when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Smart TV Video Player');
    new VideoPlayer();
});

// Prevent right-click context menu
document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
});