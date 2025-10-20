class FileManager {
    constructor() {
        this.currentFilter = 'all';
        this.files = [];
        this.initDragAndDrop();
        this.initFileInput();
        this.loadFiles();
    }
    
    initDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => uploadArea.classList.add('dragover'), false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => uploadArea.classList.remove('dragover'), false);
        });
        
        uploadArea.addEventListener('drop', (e) => this.handleDrop(e), false);
        uploadArea.addEventListener('click', () => document.getElementById('fileInput').click());
    }
    
    initFileInput() {
        const fileInput = document.getElementById('fileInput');
        fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    }
    
    async handleFiles(files) {
        const fileArray = Array.from(files);
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');
        const uploadStatus = document.getElementById('uploadStatus');
        
        if (fileArray.length === 0) return;
        
        progressBar.style.display = 'block';
        uploadStatus.style.display = 'block';
        uploadStatus.textContent = `Uploading ${fileArray.length} file(s)...`;
        
        let completed = 0;
        const total = fileArray.length;
        
        for (const file of fileArray) {
            try {
                await this.uploadFile(file);
                completed++;
                
                const progress = (completed / total) * 100;
                progressFill.style.width = `${progress}%`;
                uploadStatus.textContent = `Uploaded ${completed} of ${total} files`;
                
            } catch (error) {
                console.error(`Failed to upload ${file.name}:`, error);
                uploadStatus.textContent = `Error uploading ${file.name}: ${error.message}`;
            }
        }
        
        if (completed === total) {
            uploadStatus.textContent = `Successfully uploaded ${completed} file(s)`;
            setTimeout(() => {
                progressBar.style.display = 'none';
                uploadStatus.style.display = 'none';
                progressFill.style.width = '0%';
            }, 3000);
            
            this.loadFiles(); // Refresh file list
        }
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/admin/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Upload failed');
        }
        
        return data;
    }
    
    async loadFiles() {
        const filesGrid = document.getElementById('filesGrid');
        filesGrid.innerHTML = '<div class="loading">Loading files...</div>';
        
        try {
            const response = await fetch('/admin/api/files');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.files = data.files;
            this.renderFiles();
            
        } catch (error) {
            console.error('Failed to load files:', error);
            filesGrid.innerHTML = `<div class="no-files">Failed to load files: ${error.message}</div>`;
        }
    }
    
    renderFiles() {
        const filesGrid = document.getElementById('filesGrid');
        
        let filteredFiles = this.files;
        if (this.currentFilter !== 'all') {
            filteredFiles = this.files.filter(file => file.type === this.currentFilter);
        }
        
        if (filteredFiles.length === 0) {
            filesGrid.innerHTML = '<div class="no-files">No files found</div>';
            return;
        }
        
        filesGrid.innerHTML = filteredFiles.map(file => `
            <div class="file-card">
                <div class="file-thumbnail">
                    <img src="${file.thumbnail}" alt="${file.name}" 
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                    <div class="file-placeholder" style="display: none;">
                        <i class="fa-solid ${file.type === 'video' ? 'fa-video' : 'fa-file'}"></i>
                    </div>
                </div>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-meta">
                        <span class="file-type ${file.type}">${file.type}</span>
                        <span>${this.formatFileSize(file.size)}</span>
                    </div>
                </div>
                <div class="file-actions">
                    <button class="action-btn play-btn" onclick="fileManager.playFile('${file.name}')">
                        <i class="fa-solid fa-play"></i> Play
                    </button>
                    <button class="action-btn delete-btn" onclick="fileManager.deleteFile('${file.type}', '${file.name}')">
                        <i class="fa-solid fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    async playFile(filename) {
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
            
            alert(`Now playing: ${filename}`);
            
        } catch (error) {
            console.error('Failed to play file:', error);
            alert(`Failed to play ${filename}: ${error.message}`);
        }
    }
    
    async deleteFile(fileType, filename) {
        if (!confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
            return;
        }
        
        try {
            const response = await fetch(`/admin/api/delete/${fileType}/${filename}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            alert(`Successfully deleted: ${filename}`);
            this.loadFiles(); // Refresh file list
            
        } catch (error) {
            console.error('Failed to delete file:', error);
            alert(`Failed to delete ${filename}: ${error.message}`);
        }
    }
    
    filterFiles(filter) {
        this.currentFilter = filter;
        
        // Update active tab
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        event.target.classList.add('active');
        
        this.renderFiles();
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
}

// Global functions for button clicks
const fileManager = new FileManager();

function loadFiles() {
    fileManager.loadFiles();
}

function filterFiles(filter) {
    fileManager.filterFiles(filter);
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