let socket;
let currentAnimation = null;
let mediaFiles = [];

// Initialize WebSocket connection
function initializeSocket() {
    // Socket.IO connects to the main Flask-SocketIO server (same port as web interface)
    socket = io();  // Uses same port and protocol as current page
    
    socket.on('connect', function() {
        updateConnectionStatus(true);
        console.log('Connected to Flask-SocketIO server');
    });

    socket.on('disconnect', function() {
        updateConnectionStatus(false);
        console.log('Disconnected from Flask-SocketIO server');
    });

    socket.on('animation_changed', function(data) {
        console.log('Animation changed event:', data);
        currentAnimation = data.current_animation;
        updateMediaDisplay();
        showFeedback(`Now playing: ${data.current_animation}`);
    });

    socket.on('animation_stopped', function(data) {
        console.log('Animation stopped event:', data);
        currentAnimation = null;
        updateMediaDisplay();
        showFeedback('Animation stopped');
    });
}

// Update connection status display
function updateConnectionStatus(connected) {
    const icon = document.getElementById('connection-icon');
    const status = document.getElementById('connection-status');
    
    if (connected) {
        icon.className = 'fas fa-wifi status-connected';
        status.textContent = 'Connected';
        status.className = 'status-connected';
    } else {
        icon.className = 'fas fa-wifi-slash status-disconnected';
        status.textContent = 'Disconnected';
        status.className = 'status-disconnected';
    }
}

// Load media files
async function loadMediaFiles() {
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        mediaFiles = data.files || [];
        // Set current animation from server state
        currentAnimation = data.current_animation;
        console.log('Loaded current animation state:', currentAnimation);
        
        updateMediaDisplay();
    } catch (error) {
        console.error('Error loading media files:', error);
        showFeedback('Error loading media files', 'error');
        // Show fallback content
        document.getElementById('media-container').innerHTML = '<div class="loading">Error loading files. Please check your connection.</div>';
    }
}

// Update media display
function updateMediaDisplay() {
    const container = document.getElementById('media-container');
    
    if (mediaFiles.length === 0) {
        container.innerHTML = '<div class="loading">No animations found</div>';
        return;
    }

    console.log('Updating media display, currentAnimation:', currentAnimation);

    const grid = document.createElement('div');
    grid.className = 'media-grid';

    mediaFiles.forEach(file => {
        const isPlaying = currentAnimation === file.name;
        const item = document.createElement('div');
        item.className = `media-item ${isPlaying ? 'playing' : ''}`;
        
        // Determine icon based on file type
        const thumbIcon = file.type === 'video' ? 'fas fa-play-circle' : 'fas fa-code';
        const controlIcon = isPlaying ? 'fa-pause' : 'fa-play';
        const buttonTitle = isPlaying ? 'Currently Playing' : 'Play';
        
        console.log(`File: ${file.name}, isPlaying: ${isPlaying}, icon: ${controlIcon}`);
        
        item.innerHTML = `
            <div class="media-thumbnail" title="${buttonTitle}">
                ${file.thumbnail ? 
                    `<img src="${file.thumbnail}" alt="${file.name}">` :
                    `<i class="${thumbIcon}"></i>`
                }
                <div class="thumbnail-overlay">
                    <i class="fas ${controlIcon}"></i>
                </div>
                <div class="media-name">${file.name}</div>
            </div>
        `;

        // Add click handler and haptic feedback to entire card
        item.addEventListener('click', function() {
            playAnimation(file.name);
        });
        
        item.addEventListener('touchstart', function() {
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
        });

        grid.appendChild(item);
    });

    container.innerHTML = '';
    container.appendChild(grid);
}

// Toggle animation (play/stop)
async function toggleAnimation(filename) {
    if (currentAnimation === filename) {
        // Currently playing this animation, so stop it
        await stopAnimation();
    } else {
        // Not playing or playing different animation, so play this one
        await playAnimation(filename);
    }
}

// Play animation
async function playAnimation(filename) {
    try {
        const response = await fetch('/trigger', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ animation: filename }),
        });

        if (response.ok) {
            showFeedback(`Playing: ${filename}`);
            // Visual feedback
            if (navigator.vibrate) {
                navigator.vibrate([50, 100, 50]);
            }
        } else {
            showFeedback('Failed to play animation', 'error');
        }
    } catch (error) {
        console.error('Error playing animation:', error);
        showFeedback('Error playing animation', 'error');
    }
}

// Stop current animation
async function stopAnimation() {
    try {
        const response = await fetch('/stop', {
            method: 'POST',
        });

        if (response.ok) {
            showFeedback('Animation stopped');
            // Visual feedback
            if (navigator.vibrate) {
                navigator.vibrate(100);
            }
        } else {
            showFeedback('Failed to stop animation', 'error');
        }
    } catch (error) {
        console.error('Error stopping animation:', error);
        showFeedback('Error stopping animation', 'error');
    }
}

// Refresh media
function refreshMedia() {
    showFeedback('Refreshing...');
    loadMediaFiles();
}

// Show feedback message
function showFeedback(message, type = 'success') {
    const feedback = document.getElementById('feedback');
    feedback.textContent = message;
    feedback.style.background = type === 'error' ? 
        'rgba(244, 67, 54, 0.9)' : 'rgba(76, 175, 80, 0.9)';
    feedback.classList.add('show');
    
    setTimeout(() => {
        feedback.classList.remove('show');
    }, 3000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    loadMediaFiles();
    
    // Prevent zoom on double tap
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function (event) {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
});

// Handle orientation changes
window.addEventListener('orientationchange', function() {
    setTimeout(() => {
        updateMediaDisplay();
    }, 500);
});