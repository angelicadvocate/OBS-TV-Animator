class AdminDashboard {
    constructor() {
        this.socket = null;
        this.connectedDevices = [];
        this.isLoadingStatus = false;
        this.initWebSocket();
        this.loadStatus();
        this.startAutoRefresh();
    }
    
    initWebSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to server');
                // Register as admin dashboard
                this.socket.emit('register_admin');
                this.updateConnectionStatus(true);
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
                this.updateConnectionStatus(false);
            });
            
            this.socket.on('animation_changed', (data) => {
                console.log('Animation changed:', data);
                this.loadStatus(); // Refresh dashboard when animation changes
            });
            
            this.socket.on('devices_updated', (data) => {
                console.log('Devices updated:', data);
                this.updateDevicesList(data);
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('WebSocket connection error:', error);
                // Don't show popup for WebSocket errors as they're handled separately
            });
            
            this.socket.on('error', (error) => {
                console.error('WebSocket error:', error);
            });
            
        } catch (error) {
            console.error('WebSocket initialization failed:', error);
        }
    }
    
    async loadStatus(isRetry = false) {
        // Prevent overlapping requests
        if (this.isLoadingStatus && !isRetry) {
            console.log('Status load already in progress, skipping');
            return;
        }
        
        this.isLoadingStatus = true;
        
        try {
            const response = await fetch('/admin/api/status', {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache'
                }
            });
            
            // Check if response is ok (status 200-299)
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                // Handle authentication error specifically
                if (response.status === 401 || data.authenticated === false) {
                    console.log('Authentication expired, redirecting to login...');
                    window.location.href = '/admin/login';
                    return;
                }
                throw new Error(data.error);
            }
            
            // Success - clear any error state and update display
            this.clearErrorState();
            this.updateStatusDisplay(data);
            this.loadMediaList();
            
        } catch (error) {
            console.error('Failed to load status:', error);
            
            // Only show popup after multiple failures, not on first failure
            if (!isRetry) {
                console.log('Status load failed, attempting retry...');
                setTimeout(() => this.loadStatus(true), 2000); // Retry after 2 seconds
            } else {
                this.handleStatusError(error);
            }
        } finally {
            this.isLoadingStatus = false;
        }
    }
    
    updateStatusDisplay(data) {
        document.getElementById('totalFiles').textContent = data.total_media_count || 0;
        document.getElementById('connectedClients').textContent = data.connected_clients || 0;
        document.getElementById('animationCount').textContent = data.animations_count || 0;
        document.getElementById('videoCount').textContent = data.videos_count || 0;
        
        // Update WebSocket count (StreamerBot connections)
        document.getElementById('websocketCount').textContent = data.streamerbot_count || 0;
        
        document.getElementById('currentMediaName').textContent = data.current_media || 'None';
        document.getElementById('currentMediaType').textContent = 
            data.media_type ? `${data.media_type.toUpperCase()} File` : 'No media selected';
        
        // Update TV devices list
        this.updateTVDevicesList(data.tv_devices || [], data.connected_clients || 0);
        
        // Update StreamerBot connection status
        this.updateStreamerbotStatus(data.streamerbot_devices || [], data.streamerbot_count || 0);
        
        // Update OBS Studio connection status
        this.updateOBSStatus(data.obs_devices || [], data.obs_count || 0);
    }
    
    async loadMediaList() {
        try {
            const response = await fetch('/admin/api/files');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateMediaList(data.files);
            
        } catch (error) {
            console.error('Failed to load media list:', error);
            document.getElementById('mediaList').innerHTML = 
                '<div style="text-align: center; color: #f44336;">Failed to load media files</div>';
        }
    }
    
    updateMediaList(files) {
        const mediaList = document.getElementById('mediaList');
        
        if (files.length === 0) {
            mediaList.innerHTML = '<div style="text-align: center; opacity: 0.6;">No media files available</div>';
            return;
        }
        
        const currentMedia = document.getElementById('currentMediaName').textContent;
        
        mediaList.innerHTML = files.map(file => `
            <div class="media-item ${file.name === currentMedia ? 'active' : ''}">
                <div class="media-info">
                    <div class="media-filename">${file.name}</div>
                    <div class="media-type-badge">${file.type.toUpperCase()} • ${this.formatFileSize(file.size)}</div>
                </div>
                <button class="play-btn ${file.name === currentMedia ? 'playing' : ''}" onclick="dashboard.playMedia('${file.name}')">
                    ${file.name === currentMedia ? '<i class="fa-solid fa-pause"></i> Playing' : '<i class="fa-solid fa-play"></i> Play'}
                </button>
            </div>
        `).join('');
    }
    
    async playMedia(filename) {
        try {
            const response = await fetch('/trigger', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ animation: filename })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            console.log('Media triggered:', data);
            this.loadStatus(); // Refresh to show new current media
            
        } catch (error) {
            console.error('Failed to play media:', error);
            this.showError(`Failed to play ${filename}`);
        }
    }
    
    updateConnectionStatus(connected) {
        // This method is now handled by updateDevicesList
        console.log('Dashboard connection status:', connected ? 'Connected' : 'Disconnected');
    }
    
    updateTVDevicesList(tvDevices, tvCount) {
        const tvDevicesList = document.getElementById('tvDevicesList');
        const tvStatus = document.getElementById('tvDeviceStatus');
        
        if (tvDevices.length === 0) {
            tvDevicesList.innerHTML = `
                <div class="connected-devices">
                    <span class="device-indicator disconnected"></span>
                    <span>No TV/Displays connected</span>
                </div>
            `;
        } else {
            tvDevicesList.innerHTML = `
                <div class="connected-devices">
                    <span class="device-indicator connected"></span>
                    <span>${tvCount} TV/Display${tvCount !== 1 ? 's' : ''} connected</span>
                </div>
            `;
        }
    }

    updateStreamerbotStatus(streamerbotDevices, streamerbotCount) {
        const indicator = document.getElementById('streamerbotIndicator');
        const status = document.getElementById('streamerbotStatus');
        
        if (streamerbotCount === 0) {
            indicator.className = 'device-indicator disconnected';
            status.textContent = 'Not Connected';
        } else {
            indicator.className = 'device-indicator connected';
            status.textContent = `Connected (${streamerbotCount} connection${streamerbotCount !== 1 ? 's' : ''})`;
        }
    }

    updateOBSStatus(obsDevices, obsCount) {
        // Use existing OBS status endpoint from OBS management page
        this.fetchOBSStatus();
    }

    async fetchOBSStatus() {
        try {
            const response = await fetch('/api/obs/status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            const indicator = document.getElementById('obsIndicator');
            const status = document.getElementById('obsStatus');
            
            if (data.success && data.connected) {
                indicator.className = 'device-indicator connected';
                status.textContent = 'Connected';
                if (data.current_scene) {
                    status.textContent = `Connected - Scene: ${data.current_scene}`;
                }
            } else {
                indicator.className = 'device-indicator disconnected';
                status.textContent = data.disabled ? 'Disabled' : 'Not Connected';
                if (data.error && !data.disabled) {
                    status.textContent = 'Connection Failed';
                }
            }
        } catch (error) {
            console.error('Failed to fetch OBS status:', error);
            const indicator = document.getElementById('obsIndicator');
            const status = document.getElementById('obsStatus');
            indicator.className = 'device-indicator disconnected';
            status.textContent = 'Not Connected';
        }
    }

    // Legacy method for WebSocket events - now delegates to specific methods
    updateDevicesList(devicesInfo) {
        if (devicesInfo.tv_devices) {
            this.updateTVDevicesList(devicesInfo.tv_devices, devicesInfo.tv_count);
        }
        if (devicesInfo.streamerbot_devices) {
            this.updateStreamerbotStatus(devicesInfo.streamerbot_devices, devicesInfo.streamerbot_count);
        }
    }
    
    formatConnectionTime(timestamp) {
        const now = Date.now() / 1000;
        const diff = Math.floor(now - timestamp);
        
        if (diff < 60) return `${diff}s ago`;
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    handleStatusError(error) {
        // Only show popup for persistent errors, not temporary network issues
        const errorMessage = error.message.toLowerCase();
        
        if (errorMessage.includes('networkerror') || 
            errorMessage.includes('fetch') || 
            errorMessage.includes('connection') ||
            errorMessage.includes('timeout')) {
            console.warn('Network connectivity issue detected, will retry on next refresh cycle');
            this.showNetworkError();
        } else {
            this.showError('Failed to load server status: ' + error.message);
        }
    }
    
    showNetworkError() {
        // Show a less intrusive notification for network issues
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = 'Connection issue detected';
            statusElement.style.color = '#f44336';
        }
    }
    
    clearErrorState() {
        // Clear any error indicators when successfully connected
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = 'Connected';
            statusElement.style.color = '#4caf50';
        }
    }
    
    showError(message) {
        // Only show alert for serious errors, not network hiccups
        console.error('Dashboard error:', message);
        
        // Use a less intrusive notification if available, otherwise alert
        if (typeof showNotification === 'function') {
            showNotification(message, 'error');
        } else {
            alert(message);
        }
    }
    
    startAutoRefresh() {
        // Refresh status every 30 seconds, but prevent overlapping requests
        setInterval(() => {
            if (!this.isLoadingStatus) {
                this.loadStatus();
            } else {
                console.log('Skipping status refresh - previous request still in progress');
            }
        }, 30000);
    }
}

// Global functions for button clicks
const dashboard = new AdminDashboard();

function refreshStatus() {
    dashboard.loadStatus();
}

function openTVView() {
    window.open('/', '_blank');
}

function showRestartDialog() {
    if (confirm('Are you sure you want to restart the server? This will disconnect all devices temporarily.')) {
        alert('Server restart functionality would be implemented here');
    }
}

// Theme functions moved to global.js

// Close credentials warning
function closeWarning() {
    const warning = document.getElementById('credentialsWarning');
    if (warning) {
        warning.style.animation = 'slideUp 0.3s ease-in';
        setTimeout(() => {
            warning.remove();
        }, 300);
    }
}

// Mascot Easter Egg Functionality
document.addEventListener('DOMContentLoaded', function() {
    const mascot = document.querySelector('.floating-mascot');
    const popover = document.getElementById('mascot-message');
    
    // Initialize mascot easter egg
    
    if (mascot && popover) {
        // Track easter egg discovery
        let easterEggFound = localStorage.getItem('mascotEasterEggFound') === 'true';

        
        // Add subtle hint for undiscovered easter egg
        if (!easterEggFound) {
            mascot.style.filter += ' brightness(1.1)';
            mascot.title = 'Something magical might happen if you click me... 🎭';
        } else {
            mascot.title = 'Thanks for finding the easter egg! 🎉';
        }
        
        // Add click listener to test basic functionality
        mascot.addEventListener('click', function(e) {
            console.log('🖱️ Mascot clicked!');
            console.log('Popover element:', popover);
            console.log('Popover popover attribute:', popover.getAttribute('popover'));
            console.log('Mascot popovertarget:', mascot.getAttribute('popovertarget'));
            
            // Test if popover API is actually working
            if (popover.showPopover) {
                console.log('📋 showPopover method exists');
                try {
                    console.log('🔄 Attempting to show popover manually...');
                    popover.showPopover();
                    console.log('✅ Popover shown successfully');
                } catch (error) {
                    console.error('❌ Error showing popover:', error);
                }
            } else {
                console.log('❌ showPopover method not available');
            }
        });
        
        // Check if browser supports Popover API
        if ('popover' in HTMLElement.prototype && popover.showPopover) {
            console.log('✅ Using native Popover API');
            console.log('Popover support check - popover in HTMLElement:', 'popover' in HTMLElement.prototype);
            console.log('Popover support check - showPopover method:', !!popover.showPopover);
            
            // Listen for popover show event
            popover.addEventListener('toggle', function(e) {
                console.log('🔄 Popover toggle event fired:', e.newState);
                if (e.newState === 'open') {
                    console.log('🎉 Easter egg discovered!');
                    
                    if (!easterEggFound) {
                        localStorage.setItem('mascotEasterEggFound', 'true');
                        easterEggFound = true;
                        mascot.title = 'Thanks for finding the easter egg! 🎉';
                        mascot.style.filter = 'drop-shadow(0 4px 8px var(--shadow-primary))'; // Remove brightness hint
                        console.log('💾 Easter egg discovery saved to localStorage');
                    }
                    
                    // Add special animation when opened
                    popover.style.animation = 'popoverFadeIn 0.3s ease-out';
                }
            });
            
        } else {
            // Fallback for browsers without Popover API support
            popover.style.display = 'none';
            popover.style.position = 'fixed';
            popover.style.zIndex = '10000';
            
            mascot.addEventListener('click', function(e) {
                e.preventDefault();
                
                if (popover.style.display === 'none') {
                    // Position near mascot
                    const rect = mascot.getBoundingClientRect();
                    popover.style.display = 'block';
                    popover.style.left = (rect.left - 150) + 'px';
                    popover.style.top = (rect.top + 50) + 'px';
                    
                    if (!easterEggFound) {
                        localStorage.setItem('mascotEasterEggFound', 'true');
                        easterEggFound = true;
                        mascot.title = 'Thanks for finding the easter egg! 🎉';
                        mascot.style.filter = 'drop-shadow(0 4px 8px var(--shadow-primary))'; // Remove brightness hint
                    }
                } else {
                    popover.style.display = 'none';
                }
            });
            
            // Close button for fallback
            const closeBtn = popover.querySelector('.popover-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', function() {
                    popover.style.display = 'none';
                });
            }
            
            // Click outside to close (fallback)
            document.addEventListener('click', function(e) {
                if (!popover.contains(e.target) && !mascot.contains(e.target)) {
                    popover.style.display = 'none';
                }
            });
        }
        
        // Enhanced hover effect for discovered easter egg
        mascot.addEventListener('mouseenter', function() {
            if (easterEggFound) {
                this.style.animation = 'float 1s ease-in-out infinite';
            }
        });
        
        mascot.addEventListener('mouseleave', function() {
            this.style.animation = 'float 3s ease-in-out infinite';
        });
        
    } else {
        console.log('❌ Mascot easter egg elements not found');
    }
});