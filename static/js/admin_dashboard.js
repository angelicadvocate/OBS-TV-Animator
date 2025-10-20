class AdminDashboard {
    constructor() {
        this.socket = null;
        this.connectedDevices = [];
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
            
        } catch (error) {
            console.error('WebSocket initialization failed:', error);
        }
    }
    
    async loadStatus() {
        try {
            const response = await fetch('/admin/api/status');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.updateStatusDisplay(data);
            this.loadMediaList();
            
        } catch (error) {
            console.error('Failed to load status:', error);
            this.showError('Failed to load server status');
        }
    }
    
    updateStatusDisplay(data) {
        document.getElementById('totalFiles').textContent = data.total_media_count || 0;
        document.getElementById('connectedClients').textContent = data.connected_clients || 0;
        document.getElementById('animationCount').textContent = data.animations_count || 0;
        document.getElementById('videoCount').textContent = data.videos_count || 0;
        
        document.getElementById('currentMediaName').textContent = data.current_media || 'None';
        document.getElementById('currentMediaType').textContent = 
            data.media_type ? `${data.media_type.toUpperCase()} File` : 'No media selected';
        
        // Update devices list if available
        if (data.tv_devices) {
            this.updateDevicesList({
                tv_devices: data.tv_devices,
                tv_count: data.connected_clients
            });
        }
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
                <button class="play-btn" onclick="dashboard.playMedia('${file.name}')">
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
    
    updateDevicesList(devicesInfo) {
        const devicesList = document.getElementById('connectedDevicesList');
        const tvDevices = devicesInfo.tv_devices || [];
        
        if (tvDevices.length === 0) {
            // No devices connected
            devicesList.innerHTML = `
                <div class="connected-devices">
                    <span class="device-indicator disconnected"></span>
                    <div class="device-info">
                        <div>No devices connected</div>
                        <div class="device-type">Waiting for device...</div>
                    </div>
                </div>
            `;
        } else {
            // Show each connected device
            devicesList.innerHTML = tvDevices.map(device => `
                <div class="connected-devices">
                    <span class="device-indicator connected"></span>
                    <div class="device-info">
                        <div>Device Connected</div>
                        <div class="device-id">${device.id}</div>
                        <div class="device-type">Connected ${this.formatConnectionTime(device.connected_at)}</div>
                    </div>
                </div>
            `).join('');
        }
        
        // Store for reference
        this.connectedDevices = tvDevices;
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
    
    showError(message) {
        // Simple error display - could be enhanced with a proper notification system
        alert(message);
    }
    
    startAutoRefresh() {
        // Refresh status every 30 seconds
        setInterval(() => {
            this.loadStatus();
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

// Dark Mode Functions
function toggleDarkMode() {
    const body = document.body;
    const themeIcon = document.getElementById('themeIcon');
    
    body.classList.toggle('dark-mode');
    
    if (body.classList.contains('dark-mode')) {
        themeIcon.className = 'fa-solid fa-sun';
        localStorage.setItem('darkMode', 'enabled');
    } else {
        themeIcon.className = 'fa-solid fa-moon';
        localStorage.setItem('darkMode', 'disabled');
    }
}

function initializeDarkMode() {
    const darkMode = localStorage.getItem('darkMode');
    const body = document.body;
    const themeIcon = document.getElementById('themeIcon');
    
    if (darkMode === 'enabled') {
        body.classList.add('dark-mode');
        if (themeIcon) {
            themeIcon.className = 'fa-solid fa-sun';
        }
    }
}

// Initialize dark mode on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeDarkMode();
});