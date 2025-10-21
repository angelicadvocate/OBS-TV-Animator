/* =============================================================================
   Admin User Management JavaScript
   Handles user creation, password changes, and user list management
   ============================================================================= */

class UserManager {
    constructor() {
        this.currentUser = null;
        this.users = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadUsers();
    }

    setupEventListeners() {
        // Form submissions
        document.getElementById('addUserForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAddUser();
        });

        document.getElementById('changePasswordForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleChangePassword();
        });

        // Real-time password confirmation validation
        document.getElementById('confirmPassword').addEventListener('input', (e) => {
            this.validatePasswordMatch('newPassword', 'confirmPassword');
        });

        document.getElementById('confirmNewPassword').addEventListener('input', (e) => {
            this.validatePasswordMatch('newPasswordChange', 'confirmNewPassword');
        });

        // Input validation styling
        const inputs = document.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', () => this.updateInputValidation(input));
            input.addEventListener('blur', () => this.updateInputValidation(input));
        });
    }

    validatePasswordMatch(passwordId, confirmId) {
        const password = document.getElementById(passwordId).value;
        const confirm = document.getElementById(confirmId).value;
        const confirmInput = document.getElementById(confirmId);
        
        if (confirm && password !== confirm) {
            confirmInput.setCustomValidity('Passwords do not match');
            confirmInput.classList.add('form-error');
            confirmInput.classList.remove('form-success');
        } else {
            confirmInput.setCustomValidity('');
            confirmInput.classList.remove('form-error');
            if (confirm) {
                confirmInput.classList.add('form-success');
            }
        }
    }

    updateInputValidation(input) {
        if (input.validity.valid && input.value) {
            input.classList.add('form-success');
            input.classList.remove('form-error');
        } else if (!input.validity.valid && input.value) {
            input.classList.add('form-error');
            input.classList.remove('form-success');
        } else {
            input.classList.remove('form-success', 'form-error');
        }
    }

    async loadUsers() {
        try {
            const response = await fetch('/admin/api/users');
            const data = await response.json();
            
            if (data.success) {
                this.users = data.users;
                this.currentUser = data.current_user;
                this.renderUsers();
            } else {
                this.showError('Failed to load users: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading users:', error);
            this.showError('Failed to load users');
        }
    }

    async handleAddUser() {
        const form = document.getElementById('addUserForm');
        const formData = new FormData(form);
        
        // Validate password match
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');
        
        if (password !== confirmPassword) {
            this.showError('Passwords do not match');
            return;
        }

        try {
            const response = await fetch('/admin/api/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: formData.get('username'),
                    password: password
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`User "${formData.get('username')}" added successfully`);
                form.reset();
                this.loadUsers(); // Refresh the user list
            } else {
                this.showError('Failed to add user: ' + data.error);
            }
        } catch (error) {
            console.error('Error adding user:', error);
            this.showError('Failed to add user');
        }
    }

    async handleChangePassword() {
        const form = document.getElementById('changePasswordForm');
        const formData = new FormData(form);
        
        // Validate password match
        const newPassword = formData.get('newPassword');
        const confirmNewPassword = formData.get('confirmNewPassword');
        
        if (newPassword !== confirmNewPassword) {
            this.showError('New passwords do not match');
            return;
        }

        try {
            const response = await fetch('/admin/api/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    current_password: formData.get('currentPassword'),
                    new_password: newPassword
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Password changed successfully');
                form.reset();
            } else {
                this.showError('Failed to change password: ' + data.error);
            }
        } catch (error) {
            console.error('Error changing password:', error);
            this.showError('Failed to change password');
        }
    }

    async deleteUser(username) {
        if (username === this.currentUser) {
            this.showError('Cannot delete your own account');
            return;
        }

        if (!confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch('/admin/api/users', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`User "${username}" deleted successfully`);
                this.loadUsers(); // Refresh the user list
            } else {
                this.showError('Failed to delete user: ' + data.error);
            }
        } catch (error) {
            console.error('Error deleting user:', error);
            this.showError('Failed to delete user');
        }
    }

    renderUsers() {
        const usersList = document.getElementById('usersList');
        const userCount = document.getElementById('userCount');
        
        userCount.textContent = `${this.users.length} user${this.users.length !== 1 ? 's' : ''}`;
        
        if (this.users.length === 0) {
            usersList.innerHTML = '<div class="loading">No users found</div>';
            return;
        }

        usersList.innerHTML = this.users.map(user => {
            const isCurrentUser = user.username === this.currentUser;
            const canDelete = !isCurrentUser && this.users.length > 1;
            const isDefaultAdmin = user.username === 'admin';
            return `
                <div class="user-item ${isCurrentUser ? 'current-user' : ''}">
                    <div class="user-info">
                        <div class="username">
                            ${user.username}
                            ${isDefaultAdmin ? '<span class="default-badge">(DEFAULT)</span>' : '<i class="fa-solid fa-crown" style="color: var(--highlight); margin-left: 8px;" title="Administrator"></i>'}
                            ${isCurrentUser ? '<i class="fa-solid fa-user-check" style="color: var(--success-green, #4caf50); margin-left: 8px;" title="Currently Logged In"></i>' : ''}
                        </div>
                        <div class="user-meta">
                            <i class="fa-solid fa-user-shield"></i>
                            <span>Administrator</span>
                            ${user.last_login ? `• Last login: ${this.formatDate(user.last_login)}` : '• Never logged in'}
                        </div>
                    </div>
                    <div class="user-actions">
                        ${canDelete ? `
                            <button class="delete-btn" onclick="userManager.deleteUser('${user.username}')" title="Delete User">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        ` : ''}
                        ${!canDelete && !isCurrentUser ? `
                            <span class="no-delete-info" title="Cannot delete the last remaining user">
                                <i class="fa-solid fa-shield-halved" style="color: var(--text-secondary);"></i>
                            </span>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    formatDate(dateString) {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type} show`;
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }
}

// Utility function for refresh button
function refreshUsers() {
    userManager.loadUsers();
    userManager.showSuccess('User list refreshed');
}

// Initialize the user manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.userManager = new UserManager();
});