/**
 * OBS-TV-Animator Integration Library
 * 
 * Provides WebSocket connectivity, status indicators, and animation handling
 * for HTML animations in the OBS-TV-Animator system.
 * 
 * Usage:
 *   // Basic integration
 *   new OTAIntegration();
 *   
 *   // With custom main element for flash effects
 *   new OTAIntegration('myAnimationElement');
 *   
 *   // With custom options
 *   new OTAIntegration('myElement', {
 *     showStatusIndicator: true,
 *     enableFlashEffects: true,
 *     enablePageRefresh: true
 *   });
 */

class OTAIntegration {
    constructor(mainElementId = null, options = {}) {
        // Default options
        this.options = {
            showStatusIndicator: true,
            enableFlashEffects: true,
            enablePageRefresh: true,
            heartbeatInterval: 30000,
            refreshDelay: 500,
            animationChangeDelay: 1000,
            ...options
        };
        
        // Elements
        this.mainElement = mainElementId ? document.getElementById(mainElementId) : null;
        this.statusIndicator = null;
        
        // WebSocket
        this.socket = null;
        this.currentScene = this.getCurrentSceneName();
        
        // Initialize
        this.init();
    }
    
    init() {
        console.log('Initializing OBS-TV-Animator Integration...');
        
        if (this.options.showStatusIndicator) {
            this.createStatusIndicator();
        }
        
        this.initWebSocket();
        
        if (this.options.heartbeatInterval > 0) {
            this.startHeartbeat();
        }
    }
    
    getCurrentSceneName() {
        // Try to determine scene name from filename or page title
        const path = window.location.pathname;
        const filename = path.substring(path.lastIndexOf('/') + 1);
        return filename.replace('.html', '') || 'animation';
    }
    
    createStatusIndicator() {
        // Create status indicator element
        this.statusIndicator = document.createElement('div');
        this.statusIndicator.className = 'ota-status-indicator disconnected';
        this.statusIndicator.id = 'otaStatusIndicator';
        this.statusIndicator.title = 'OTA Connection Status';
        
        // Add to body
        document.body.appendChild(this.statusIndicator);
    }
    
    initWebSocket() {
        try {
            // Connect to the OBS-TV-Animator server
            const serverUrl = window.location.origin;
            this.socket = io(serverUrl);
            
            // Connection events
            this.socket.on('connect', () => {
                console.log('Connected to OBS-TV-Animator server');
                this.updateStatus('Connected', true);
                
                if (this.options.enableFlashEffects) {
                    this.flashAnimation();
                }
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
                this.updateStatus('Disconnected', false);
            });
            
            // Animation events
            this.socket.on('animation_changed', (data) => {
                console.log('Animation changed:', data);
                this.handleAnimationChange(data);
                
                // Auto-refresh page if requested (for seamless media changes)
                if (this.options.enablePageRefresh && data.refresh_page) {
                    console.log('Page refresh requested, reloading in ' + this.options.animationChangeDelay + 'ms...');
                    setTimeout(() => {
                        window.location.reload();
                    }, this.options.animationChangeDelay);
                }
            });
            
            // Listen for explicit page refresh commands
            this.socket.on('page_refresh', (data) => {
                console.log('Page refresh command received:', data);
                
                if (this.options.enablePageRefresh) {
                    this.showRefreshNotification(data);
                    setTimeout(() => {
                        window.location.reload();
                    }, this.options.refreshDelay);
                }
            });
            
            this.socket.on('status', (data) => {
                console.log('Server status:', data);
                if (data.current_animation) {
                    console.log(`Current animation: ${data.current_animation}`);
                }
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
    
    updateStatus(message, connected) {
        if (this.statusIndicator) {
            this.statusIndicator.className = connected ? 
                'ota-status-indicator connected' : 
                'ota-status-indicator disconnected';
            this.statusIndicator.title = `OTA: ${message}`;
        }
    }
    
    handleAnimationChange(data) {
        // Flash animation to indicate change
        if (this.options.enableFlashEffects) {
            this.flashAnimation();
        }
        
        // Log the change
        console.log(`Animation changed from ${data.previous_animation} to ${data.current_animation}`);
        
        // Custom callback for user handling
        if (typeof this.onAnimationChange === 'function') {
            this.onAnimationChange(data);
        }
    }
    
    showRefreshNotification(data) {
        // Show a brief notification before page refresh
        const notification = document.createElement('div');
        notification.className = 'ota-notification';
        
        notification.innerHTML = `
            <div>Loading new content...</div>
            <div class="subtitle">
                ${data.new_media || 'Unknown'} (${data.media_type || 'media'})
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
    
    flashAnimation() {
        if (!this.mainElement) return;
        
        this.mainElement.classList.remove('ota-flash-animation');
        // Force reflow
        this.mainElement.offsetHeight;
        this.mainElement.classList.add('ota-flash-animation');
        
        setTimeout(() => {
            this.mainElement.classList.remove('ota-flash-animation');
        }, 1500);
    }
    
    startHeartbeat() {
        // Request status every interval to keep connection alive
        setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('get_status');
            }
        }, this.options.heartbeatInterval);
    }
    
    // Public API methods
    
    /**
     * Manually trigger a flash animation effect
     */
    flash() {
        this.flashAnimation();
    }
    
    /**
     * Check if WebSocket is currently connected
     */
    isConnected() {
        return this.socket && this.socket.connected;
    }
    
    /**
     * Get current connection status
     */
    getStatus() {
        return {
            connected: this.isConnected(),
            scene: this.currentScene,
            socket: this.socket
        };
    }
    
    /**
     * Set custom animation change handler
     */
    setAnimationChangeHandler(callback) {
        this.onAnimationChange = callback;
    }
    
    /**
     * Disconnect and cleanup
     */
    destroy() {
        if (this.socket) {
            this.socket.disconnect();
        }
        
        if (this.statusIndicator && this.statusIndicator.parentNode) {
            this.statusIndicator.parentNode.removeChild(this.statusIndicator);
        }
    }
}

// Auto-initialize if Socket.IO is available
document.addEventListener('DOMContentLoaded', () => {
    // Check if Socket.IO is loaded
    if (typeof io === 'undefined') {
        console.warn('OTA Integration: Socket.IO not found. Please include Socket.IO library before ota-integration.js');
        return;
    }
    
    // Auto-initialize only if no manual initialization detected
    setTimeout(() => {
        if (!window.otaIntegration) {
            console.log('Auto-initializing OTA Integration...');
            window.otaIntegration = new OTAIntegration();
        }
    }, 100);
});

// Auto-refresh fallback (if WebSocket fails)
setTimeout(() => {
    if (typeof io !== 'undefined' && (!window.otaIntegration || !window.otaIntegration.isConnected())) {
        console.log('WebSocket not connected, falling back to auto-refresh in 60 seconds');
        setTimeout(() => window.location.reload(), 60000);
    }
}, 5000);

// Export for manual use
window.OTAIntegration = OTAIntegration;