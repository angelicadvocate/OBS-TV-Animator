/* =============================================================================
   OBS-TV-Animator Global JavaScript
   Share and Support Functions
   ============================================================================= */

// Project configuration
const PROJECT_CONFIG = {
    shareURL: "https://github.com/angelicadvocate/OBS-TV-Animator",
    shareText: "Check out this awesome Smart TV animation system for OBS Studio!",
    tipURL: "https://streamelements.com/angelicadvocate/tip",
    githubURL: "https://github.com/angelicadvocate/OBS-TV-Animator"
};

// Social sharing functions
function shareToTwitter() {
    const url = encodeURIComponent(PROJECT_CONFIG.shareURL);
    const text = encodeURIComponent(PROJECT_CONFIG.shareText);
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank');
}

function shareToReddit() {
    const url = encodeURIComponent(PROJECT_CONFIG.shareURL);
    const text = encodeURIComponent(PROJECT_CONFIG.shareText);
    window.open(`https://www.reddit.com/submit?url=${url}&title=${text}`, '_blank');
}

function shareToDiscord() {
    const shareContent = `${PROJECT_CONFIG.shareText}\n${PROJECT_CONFIG.shareURL}`;
    
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(shareContent).then(() => {
            showNotification("Link copied! Paste it into your favorite Discord server.", "success");
        }).catch(() => {
            fallbackCopyToClipboard(shareContent);
        });
    } else {
        fallbackCopyToClipboard(shareContent);
    }
}

function shareOnFacebook() {
    const url = encodeURIComponent(PROJECT_CONFIG.shareURL);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, "_blank");
}

function openTipPage() {
    window.open(PROJECT_CONFIG.tipURL, '_blank');
}

function openGitHubProject() {
    window.open(PROJECT_CONFIG.githubURL, '_blank');
}

// Fallback clipboard function for older browsers
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification("Link copied! Paste it into your favorite Discord server.", "success");
    } catch (err) {
        showNotification("Could not copy link. Please copy manually: " + text, "error");
    }
    
    document.body.removeChild(textArea);
}

// Notification system
function showNotification(message, type = "info") {
    // Remove any existing notifications
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '12px 20px',
        borderRadius: '8px',
        color: 'white',
        fontWeight: 'bold',
        zIndex: '9999',
        maxWidth: '300px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
        transition: 'all 0.3s ease',
        transform: 'translateX(100%)'
    });
    
    // Set background color based on type
    switch (type) {
        case 'success':
            notification.style.backgroundColor = '#10b981';
            break;
        case 'error':
            notification.style.backgroundColor = '#ef4444';
            break;
        default:
            notification.style.backgroundColor = '#3b82f6';
    }
    
    // Add to DOM and animate in
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Theme management (server-side storage)
function toggleDarkMode() {
    const body = document.body;
    const isDark = body.classList.contains('dark-mode');
    const newTheme = isDark ? 'light' : 'dark';
    
    console.log(`Theme toggle clicked. Current: ${isDark ? 'dark' : 'light'}, Switching to: ${newTheme}`);
    
    // Update UI immediately for responsiveness
    if (isDark) {
        body.classList.remove('dark-mode');
    } else {
        body.classList.add('dark-mode');
    }
    
    // Update theme toggle icon
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.className = isDark ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
    }
    
    // Save to server
    fetch('/admin/api/theme', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ theme: newTheme })
    })
    .then(response => {
        console.log('Theme save response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Theme save response:', data);
        if (data.error) {
            throw new Error(data.error);
        }
    })
    .catch(error => {
        console.error('Error saving theme:', error);
        // Revert UI change if server request fails
        if (isDark) {
            body.classList.add('dark-mode');
        } else {
            body.classList.remove('dark-mode');
        }
        if (themeIcon) {
            themeIcon.className = isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        }
    });
}

// Initialize theme on page load (theme is set by server via body class)
function initializeTheme() {
    // Theme is already set by the server via body class
    // Just need to set the correct icon
    const body = document.body;
    const isDark = body.classList.contains('dark-mode');
    const themeIcon = document.getElementById('themeIcon');
    
    console.log(`Theme initialized. Body classes: "${body.className}", isDark: ${isDark}`);
    
    if (themeIcon) {
        themeIcon.className = isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        console.log(`Theme icon set to: ${themeIcon.className}`);
    } else {
        console.log('Theme icon element not found');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    
    // Add click handlers for share buttons if they exist
    const shareButtons = {
        'shareTwitter': shareToTwitter,
        'shareFacebook': shareOnFacebook,
        'shareReddit': shareToReddit,
        'shareDiscord': shareToDiscord,
        'tipButton': openTipPage,
        'githubButton': openGitHubProject
    };
    
    Object.keys(shareButtons).forEach(buttonId => {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', shareButtons[buttonId]);
        }
    });
    
    // Add theme toggle handler
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleDarkMode);
    }
});