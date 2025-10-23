"""
Thumbnail Generation Service for OBS TV Animator

This service handles automatic thumbnail generation for:
- HTML animations using Playwright browser automation
- Video files using FFmpeg
"""

import os
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urljoin
import hashlib
import time

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available - HTML thumbnail generation disabled")

class ThumbnailService:
    """Service for generating thumbnails from HTML animations and videos"""
    
    def __init__(self, base_url: str = "http://localhost:8080", thumbnails_dir: str = "data/thumbnails"):
        self.base_url = base_url.rstrip('/')
        self.thumbnails_dir = Path(thumbnails_dir)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        # Thumbnail settings
        self.html_thumbnail_width = 320
        self.html_thumbnail_height = 180
        self.html_capture_delay = 2000  # ms to wait for animations to load
        
        self.video_thumbnail_width = 320
        self.video_thumbnail_height = 180
        self.video_capture_time = "00:00:01"  # Capture at 1 second mark
    
    def get_thumbnail_path(self, filename: str) -> Path:
        """Get the path where thumbnail should be saved"""
        # Create hash of filename to avoid filesystem issues
        name_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        safe_name = "".join(c for c in filename if c.isalnum() or c in ".-_")[:50]
        thumbnail_name = f"{safe_name}_{name_hash}.png"
        return self.thumbnails_dir / thumbnail_name
    
    def thumbnail_exists(self, filename: str, source_path: Path) -> bool:
        """Check if thumbnail exists and is newer than source file"""
        thumbnail_path = self.get_thumbnail_path(filename)
        if not thumbnail_path.exists():
            return False
        
        # Check if thumbnail is newer than source file
        try:
            thumbnail_mtime = thumbnail_path.stat().st_mtime
            source_mtime = source_path.stat().st_mtime
            return thumbnail_mtime > source_mtime
        except (OSError, FileNotFoundError):
            return False
    
    async def generate_html_thumbnail(self, filename: str, html_path: Path) -> bool:
        """Generate thumbnail for HTML animation file using Playwright"""
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.warning(f"Playwright not available - cannot generate thumbnail for {filename}")
            return False
        
        thumbnail_path = self.get_thumbnail_path(filename)
        
        try:
            # Check if we need to regenerate
            if self.thumbnail_exists(filename, html_path):
                self.logger.info(f"Thumbnail already exists and is up-to-date for {filename}, skipping generation")
                return True
            
            self.logger.info(f"Generating HTML thumbnail for {filename}")
            
            # Use local file path instead of HTTP URL
            animation_url = f"file://{html_path.resolve()}"
            
            async with async_playwright() as p:
                # Launch browser with minimal resources
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-extensions',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                    ]
                )
                
                try:
                    # Create new page with viewport size matching thumbnail dimensions
                    page = await browser.new_page(
                        viewport={
                            'width': self.html_thumbnail_width * 2,  # 2x for better quality
                            'height': self.html_thumbnail_height * 2
                        }
                    )
                    
                    # Set timeout and navigate to animation
                    page.set_default_timeout(10000)  # 10 second timeout
                    await page.goto(animation_url, wait_until='networkidle')
                    
                    # Wait for animations to start/load
                    await page.wait_for_timeout(self.html_capture_delay)
                    
                    # Take screenshot
                    await page.screenshot(
                        path=str(thumbnail_path),
                        type='png',
                        clip={
                            'x': 0,
                            'y': 0,
                            'width': self.html_thumbnail_width * 2,
                            'height': self.html_thumbnail_height * 2
                        }
                    )
                    
                    self.logger.info(f"Successfully generated HTML thumbnail: {thumbnail_path}")
                    return True
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            self.logger.error(f"Failed to generate HTML thumbnail for {filename}: {str(e)}")
            # Clean up any partial file
            if thumbnail_path.exists():
                try:
                    thumbnail_path.unlink()
                except OSError:
                    pass
            return False
    
    def generate_video_thumbnail(self, filename: str, video_path: Path) -> bool:
        """Generate thumbnail for video file using FFmpeg"""
        thumbnail_path = self.get_thumbnail_path(filename)
        
        try:
            # Check if we need to regenerate
            if self.thumbnail_exists(filename, video_path):
                self.logger.info(f"Video thumbnail already exists and is up-to-date for {filename}, skipping generation")
                return True
            
            self.logger.info(f"Generating video thumbnail for {filename}")
            
            # FFmpeg command to extract frame
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-ss', self.video_capture_time,
                '-vframes', '1',
                '-vf', f'scale={self.video_thumbnail_width}:{self.video_thumbnail_height}',
                '-y',  # Overwrite output file
                str(thumbnail_path)
            ]
            
            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully generated video thumbnail: {thumbnail_path}")
                return True
            else:
                self.logger.error(f"FFmpeg failed for {filename}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"FFmpeg timeout for {filename}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to generate video thumbnail for {filename}: {str(e)}")
            # Clean up any partial file
            if thumbnail_path.exists():
                try:
                    thumbnail_path.unlink()
                except OSError:
                    pass
            return False
    
    async def generate_thumbnail(self, filename: str, file_path: Path) -> Tuple[bool, str]:
        """
        Generate appropriate thumbnail based on file type
        Returns (success: bool, thumbnail_filename: str)
        """
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext in ['html', 'htm']:
            success = await self.generate_html_thumbnail(filename, file_path)
        elif file_ext in ['mp4', 'webm', 'mov', 'avi', 'mkv']:
            success = await asyncio.get_event_loop().run_in_executor(
                None, self.generate_video_thumbnail, filename, file_path
            )
        else:
            self.logger.warning(f"Unsupported file type for thumbnail: {filename}")
            return False, ""
        
        if success:
            thumbnail_path = self.get_thumbnail_path(filename)
            return True, thumbnail_path.name
        else:
            return False, ""
    
    def get_thumbnail_url(self, filename: str) -> Optional[str]:
        """Get the URL path for a file's thumbnail"""
        thumbnail_path = self.get_thumbnail_path(filename)
        if thumbnail_path.exists():
            return f"/admin/api/thumbnail/{filename}"
        return None
    
    def serve_thumbnail(self, filename: str) -> Optional[Path]:
        """Get the filesystem path for serving a thumbnail"""
        thumbnail_path = self.get_thumbnail_path(filename)
        return thumbnail_path if thumbnail_path.exists() else None
    
    async def generate_all_thumbnails(self, animations_dir: Path, videos_dir: Path) -> dict:
        """Generate thumbnails for all files in animations and videos directories"""
        results = {
            'html_generated': 0,
            'html_failed': 0,
            'video_generated': 0,
            'video_failed': 0,
            'html_skipped': 0,
            'video_skipped': 0
        }
        
        # Process HTML files
        if animations_dir.exists():
            for html_file in animations_dir.glob('*.html'):
                try:
                    if self.thumbnail_exists(html_file.name, html_file):
                        results['html_skipped'] += 1
                        continue
                    
                    success = await self.generate_html_thumbnail(html_file.name, html_file)
                    if success:
                        results['html_generated'] += 1
                    else:
                        results['html_failed'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Error processing HTML file {html_file.name}: {str(e)}")
                    results['html_failed'] += 1
        
        # Process video files
        if videos_dir.exists():
            video_extensions = ['*.mp4', '*.webm', '*.mov', '*.avi', '*.mkv']
            for pattern in video_extensions:
                for video_file in videos_dir.glob(pattern):
                    try:
                        if self.thumbnail_exists(video_file.name, video_file):
                            results['video_skipped'] += 1
                            continue
                        
                        success = await asyncio.get_event_loop().run_in_executor(
                            None, self.generate_video_thumbnail, video_file.name, video_file
                        )
                        if success:
                            results['video_generated'] += 1
                        else:
                            results['video_failed'] += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error processing video file {video_file.name}: {str(e)}")
                        results['video_failed'] += 1
        
        return results
    
    def cleanup_orphaned_thumbnails(self, animations_dir: Path, videos_dir: Path) -> int:
        """Remove thumbnails for files that no longer exist"""
        cleaned_count = 0
        
        # Get list of all existing files
        existing_files = set()
        
        if animations_dir.exists():
            existing_files.update(f.name for f in animations_dir.glob('*.html'))
        
        if videos_dir.exists():
            video_extensions = ['*.mp4', '*.webm', '*.mov', '*.avi', '*.mkv']
            for pattern in video_extensions:
                existing_files.update(f.name for f in videos_dir.glob(pattern))
        
        # Check each thumbnail
        for thumbnail_file in self.thumbnails_dir.glob('*.png'):
            # Try to match thumbnail back to original file
            # This is approximate since we hash filenames
            found_match = False
            
            for existing_file in existing_files:
                if self.get_thumbnail_path(existing_file).name == thumbnail_file.name:
                    found_match = True
                    break
            
            if not found_match:
                try:
                    thumbnail_file.unlink()
                    cleaned_count += 1
                    self.logger.info(f"Removed orphaned thumbnail: {thumbnail_file.name}")
                except OSError as e:
                    self.logger.error(f"Failed to remove thumbnail {thumbnail_file.name}: {str(e)}")
        
        return cleaned_count


# Global thumbnail service instance
thumbnail_service = None

def get_thumbnail_service(base_url: str = "http://localhost:8080") -> ThumbnailService:
    """Get or create the global thumbnail service instance"""
    global thumbnail_service
    if thumbnail_service is None:
        thumbnail_service = ThumbnailService(base_url=base_url)
    return thumbnail_service