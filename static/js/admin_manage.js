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
                <div class="file-left">
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
                </div>
                <div class="file-actions">
                    <button class="action-btn play-btn" onclick="fileManager.playFile('${file.name}')">
                        <i class="fa-solid fa-play"></i> Play
                    </button>
                    <button class="action-btn delete-btn" onclick="fileManager.deleteFile('${file.type}', '${file.name}')">
                        <i class="fa-solid fa-trash"></i> Delete
                    </button>
                    <button class="action-btn streamerbot-btn" onclick="fileManager.copyStreamerbotCS('${file.name}')" title="Copy StreamerBot C# code to clipboard">
                        <i class="fa-solid fa-code"></i> StreamerBot C#
                    </button>
                    <button class="action-btn streamerbot-btn" onclick="fileManager.copyStreamerbotHTTP('${file.name}')" title="Copy StreamerBot HTTP URL to clipboard">
                        <i class="fa-solid fa-link"></i> StreamerBot HTTP
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
    
    copyStreamerbotCS(filename) {
        const csCode = `using System;
using System.Net.Http;
using System.Text;

public class CPHInline
{
    public bool Execute()
    {
        CPH.LogInfo("Starting animation trigger...");
        
        try
        {
            using (var client = new HttpClient())
            {
                client.Timeout = TimeSpan.FromSeconds(5);
                
                var url = "http://localhost:8080/trigger";
                var json = "{\\"animation\\":\\"${filename}\\"}";
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                CPH.LogInfo($"Sending POST to: {url}");
                
                var response = client.PostAsync(url, content).Result;
                
                if (response.IsSuccessStatusCode)
                {
                    var responseBody = response.Content.ReadAsStringAsync().Result;
                    CPH.LogInfo($"SUCCESS: {responseBody}");
                    return true;
                }
                else
                {
                    CPH.LogError($"FAILED: {response.StatusCode} - {response.ReasonPhrase}");
                    return false;
                }
            }
        }
        catch (Exception ex)
        {
            CPH.LogError($"ERROR: {ex.Message}");
            return false;
        }
    }
}`;

        this.copyToClipboard(csCode, `StreamerBot C# code for ${filename}`);
    }
    
    copyStreamerbotHTTP(filename) {
        const httpUrl = `http://localhost:8080/trigger?animation=${filename}`;
        this.copyToClipboard(httpUrl, `StreamerBot HTTP URL for ${filename}`);
    }
    
    copyToClipboard(text, description) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                this.showNotification(`✅ ${description} copied to clipboard!`, 'success');
            }).catch(() => {
                this.fallbackCopyToClipboard(text, description);
            });
        } else {
            this.fallbackCopyToClipboard(text, description);
        }
    }
    
    fallbackCopyToClipboard(text, description) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            this.showNotification(`✅ ${description} copied to clipboard!`, 'success');
        } catch (err) {
            this.showNotification(`❌ Failed to copy ${description}. Please try again.`, 'error');
        } finally {
            document.body.removeChild(textArea);
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        if (notification) {
            notification.textContent = message;
            notification.className = `notification ${type} show`;
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        } else {
            // Fallback to alert if notification system isn't available
            alert(message);
        }
    }
    
    // Thumbnail Management Functions
    async generateAllThumbnails() {
        const button = document.getElementById('generateThumbnailsBtn');
        const originalText = button.innerHTML;
        
        try {
            // Disable button and show loading
            button.disabled = true;
            button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
            
            const response = await fetch('/admin/api/thumbnails/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('✅ Thumbnail generation started! This may take a few minutes.', 'success');
                
                // Auto-refresh status after a delay
                setTimeout(() => {
                    this.checkThumbnailStatus();
                }, 5000);
            } else {
                this.showNotification(`❌ Failed to start thumbnail generation: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`❌ Error generating thumbnails: ${error.message}`, 'error');
        } finally {
            // Re-enable button
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
    
    async checkThumbnailStatus() {
        const statusDiv = document.getElementById('thumbnailStatus');
        const button = document.getElementById('thumbnailStatusBtn');
        const originalText = button.innerHTML;
        
        try {
            // Show loading state
            button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Checking...';
            
            const response = await fetch('/admin/api/thumbnails/status');
            const status = await response.json();
            
            if (response.ok) {
                // Update status display
                document.getElementById('totalFiles').textContent = status.total_files;
                document.getElementById('htmlFiles').textContent = status.html_files;
                document.getElementById('videoFiles').textContent = status.video_files;
                document.getElementById('thumbnailCount').textContent = status.thumbnail_count;
                document.getElementById('completionPercentage').textContent = status.completion_percentage + '%';
                
                // Show the status section
                statusDiv.style.display = 'block';
                
                this.showNotification('✅ Thumbnail status updated!', 'success');
            } else {
                this.showNotification(`❌ Failed to get thumbnail status: ${status.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`❌ Error checking thumbnail status: ${error.message}`, 'error');
        } finally {
            // Reset button
            button.innerHTML = originalText;
        }
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

// Theme functions are handled by global.js

// Initialize page on load
document.addEventListener('DOMContentLoaded', () => {
    // Theme initialization is handled by global.js
    
    // Initialize thumbnail management buttons
    const generateBtn = document.getElementById('generateThumbnailsBtn');
    const statusBtn = document.getElementById('thumbnailStatusBtn');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', () => {
            fileManager.generateAllThumbnails();
        });
    }
    
    if (statusBtn) {
        statusBtn.addEventListener('click', () => {
            fileManager.checkThumbnailStatus();
        });
    }
});