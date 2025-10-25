
# OBS-TV-Animator TODO List

## Priority: High (Security & Production Ready)

- [ ] **Fix production deployment issues**
  - Use eventlet or gevent, remove 'allow_unsafe_werkzeug=True' from app.py
  - Replace development Flask server with proper production WSGI server (gunicorn)
  - Update Docker configuration for production deployment

## Priority: Medium (Integration & Features)

- [ ] **Add OBS WebSocket Client Integration**
  - Research and implement `obs-websocket-py` library integration
  - Add OBS WebSocket client functionality to Flask server (OBS acts as server, we connect as client)
  - Enable bidirectional OBS communication (scene detection, control commands)
  - Architecture: Our Flask App → connects to → OBS WebSocket Server (port 4455/4444)
  - **NOTE**: OBS cannot connect to external servers, only acts as WebSocket server
  - Integration will enable scene change detection and automated scene switching
  - **Add "Manage OBS Server" button to Quick Actions card** - replace "Manage Users" button to avoid layout changes
  - Button should allow configuration of OBS WebSocket server settings (host, port, password)
  - Update README screenshot after OBS management button is added

## Priority: Low (Code Organization & Cleanup)

- [ ] **OBS Studio Instructions Page Review**
  - Must be done after `obs-websocket-py` library integration
  - Review and update OBS Studio instruction page once WebSocket integration is implemented
  - Update screenshots and examples to reflect new WebSocket connection method
  - Remove outdated browser source references if any remain
  - Ensure instructions align with new OBS WebSocket client functionality
  - Add troubleshooting section specific to OBS WebSocket connection issues

- [ ] **Update StreamerBot "Common Stream Events" animation suggestions**
  - Must be done after starter animation templates are complete
  - Review and update the "Suggested Animation" recommendations in the StreamerBot integration page
  - Replace generic anim1-4.html suggestions with more specific, purpose-built animations
  - Align suggestions with expanded starter animation library after more animations are built
  - Consider event-specific animations (follow celebrations, donation displays, raid entrances, etc.)

- [ ] **Add StreamerBot Sample Integrations section with import strings**
  - Must be done after starter animation templates are complete
  - Import string must be generated in streamerbot
  - Create "Sample Integrations" section in StreamerBot integration page
  - Add copy-to-clipboard StreamerBot import string for instant setup examples
  - Include pre-configured actions for common events (Follow, Donation, Raid, Subscribe)
  - Actions should reference the base animations that ship with the project
  - Users can click "Import Actions" in StreamerBot and paste the JSON for instant working examples
  - Provide both C# WebSocket and HTTP Fetch URL action examples
  - Include proper trigger configurations and sub-action setup in the import data

- [ ] **Audit HTML templates for inline CSS/JS separation**
  - Review all HTML templates in /templates/ directory for inline `<style>` and `<script>` tags
  - Identify templates that still have inline CSS or JavaScript that should be moved to separate files
  - Extract inline styles to page-specific CSS files in /static/css/
  - Extract inline scripts to page-specific JS files in /static/js/
  - Update template references to use external files for better maintainability and caching
  - Ensure consistent code organization across all templates

## Priority: Low (Animation Template Ideas)

- [ ] **Subscriber celebration with profile image integration**
  - StreamerBot integration to capture new subscriber events
  - Dynamic profile image display from Twitch/YouTube API
  - Personalized confetti animation with subscriber's avatar
  - WebSocket data flow: StreamerBot → Flask server → Animation
  - Real-world example of event-driven, data-rich animations

- [ ] **Additional template ideas for future development**
  - "Welcome Raiders" screen for background scene visibility
  - Goal progress tracker with dynamic updates
  - "Starting Soon" countdown with streamer branding
  - Technical difficulties holding screen
  - New follower celebration burst animation

## Priority: Low (Additional Features)

## Completed Items

- [x] **Repository cleanup** ✨ *COMPLETED*
  - Removed all unnecessary testing files from main repo (test_streamerbot_connection.py, test_websocket_client.py)
  - Cleaned up personal project notes (Z_project_notes.md)
  - Removed all batch/shell script wrappers (dev-local.bat, dev-server.bat, dev-server.sh, prod-server.bat)
  - Archived and removed z_extras research files (8 StreamerBot .cs files, websocket research docs)
  - Deleted outdated documentation (USAGE.md - content moved to instruction pages)
  - Removed Docker helper scripts (start-docker.bat, start-docker.sh)
  - Moved ALL development-specific files to z_extras (DEVELOPMENT.md, docker-compose.dev.yml, dev_local.py)
  - Modified dev_local.py to work from z_extras location with proper path resolution
  - Added usage instructions to docker-compose.dev.yml for moving to root before use
  - Updated DEVELOPMENT.md with correct paths and commands for relocated files
  - Retained useful utilities (example_trigger.py, file_trigger_watcher.py, .env.example, todo_list.md)
  - Achieved completely clean repository root with only production files
  - All files backed up before deletion for recovery if needed

- [x] **Update StreamerBot setup instructions** ✨ *COMPLETED*
  - Added comprehensive instructions for creating Actions and Sub-Actions in StreamerBot
  - Documented both HTTP (Fetch URL) and C# (Execute C# Code) integration methods with complete examples
  - Simplified workflow to GUI-focused approach (Create → Define Trigger → Add Sub-Action)
  - Added basic and advanced setup examples for common event triggers
  - Comprehensive troubleshooting section including C# execution failure debugging
  - Integrated copy-to-clipboard functionality in Manage Files page for ready-to-use code
  - Fixed Jinja2 template syntax errors with {% raw %} blocks around C# code
  - Replaced emojis with Font Awesome icons for visual consistency
  - Decided against screenshot maintenance burden and overly technical GET/POST explanations
  - StreamerBot's built-in variable randomization preferred over custom server endpoint

- [x] **Documentation Review & Cleanup** ✨ *COMPLETED*
  - Reviewed all instruction pages (Getting Started, StreamerBot, Troubleshooting) for accuracy
  - Fixed outdated references, broken links, and confusing sections in troubleshooting page
  - Updated all code examples and URLs to be current and working (port references, Docker commands)
  - Ensured mobile responsiveness of instruction pages with proper styling
  - Replaced emojis with Font Awesome icons for visual consistency across all pages
  - Fixed Jinja2 template syntax errors in StreamerBot integration page
  - Updated Smart TV connection troubleshooting to reflect actual architecture vs outdated browser source references
  - Added comprehensive backup/restore instructions with bind mount alternatives
  - Standardized success banner styling and page structure across all instruction pages

- [x] **Implement Automatic Thumbnail Generation** ✨ *COMPLETED*
  - Added Playwright to Docker container for HTML animation screenshots
  - Implemented FFmpeg integration for video file thumbnail extraction
  - Created comprehensive thumbnail generation service (thumbnail_service.py)
  - Added thumbnail storage directory structure (data/thumbnails/)
  - Updated file API to serve real thumbnail URLs instead of placeholders
  - Integrated thumbnail generation into upload process (both drag-drop and file input)
  - Added fallback system for files without thumbnails and error handling
  - Optimized thumbnail size and quality (320x180px for both HTML and video)
  - Docker container properly configured with Playwright browsers and FFmpeg
  - Automatic cleanup system for orphaned thumbnails

- [x] **Admin Dashboard UI/UX Improvements** ✨ *COMPLETED*
  - Enhanced button styling with improved opacity (30%) for better visibility
  - Fixed theme synchronization conflicts between admin pages
  - Implemented retry logic for "Failed to load server status" error handling
  - Added real-time StreamerBot connection status tracking and display
  - Restructured dashboard layout with 2×3 status grid for better organization
  - Repositioned Available Media card before Quick Actions for improved flow
  - Added OBS Studio connection status section with placeholder functionality
  - Enhanced Quick Actions card with "Manage Users" button (6 total actions)
  - Optimized spacing in device sections to minimize scrollbar visibility
  - Updated README documentation with current dashboard screenshot

- [x] **StreamerBot Integration Helper in File Management** ✨ *COMPLETED*
  - Added "StreamerBot C#" button next to each animation file in manage files page
  - Added "StreamerBot HTTP" button for legacy HTTP trigger support
  - Implemented copy-to-clipboard functionality for both C# code and HTTP configuration
  - Generated file-specific C# code with animation variables dynamically inserted
  - Users can copy-paste complete ready-to-use C# Execute Code directly into StreamerBot
  - Added HTTP URL configuration with complete setup instructions
  - Blue button styling to distinguish from play/delete actions
  - Mobile-responsive layout for 4 buttons per file
  - Comprehensive error handling and user feedback notifications
  - Both WebSocket and HTTP integration methods supported

- [x] **Fix header logo mobile responsiveness** ✨ *COMPLETED*
  - Added media query for screens under 500px width
  - Reduced logo text size by 20% on mobile devices (2rem → 1.6rem for admin pages)
  - Fixed login page header scaling (1.9rem → 1.52rem for login page)
  - Ensures proper logo visibility and prevents text cutoff on small screens
  - Applied globally across all admin pages and login screen

- [x] **Add preview images to README.md** ✨ *COMPLETED*
  - Added admin dashboard screenshot showing user management interface
  - Included GIF demonstration of HTML/CSS animation switching
  - Included GIF demonstration of video animation playback
  - Enhanced README with visual preview section for better project understanding

- [x] **Create comprehensive documentation** ✨ *COMPLETED*
  - Update README.md as quick setup guide with Docker instructions
  - Add note in README to see detailed usage page in admin panel after deployment
  - Create installation, setup, and usage instructions page in admin portal

- [x] **Fix mobile responsiveness** ✨ *COMPLETED*
  - Fixed text overflow issues in instruction cards on mobile devices
  - Added comprehensive mobile CSS with word wrapping and overflow handling
  - Implemented responsive breakpoints (768px, 600px) with proper text constraints
  - Enhanced mobile user experience with better text readability

- [x] **Add instructions/usage page to admin interface** ✨ *COMPLETED*
  - Setup instructions for OBS Studio integration
  - StreamerBot configuration and webhook setup
  - Manual terminal/PowerShell command examples for testing
  - WebSocket API documentation and examples

- [x] **Repurpose redundant refresh button as instructions button** ✨ *COMPLETED*
  - Convert the refresh button in "Quick Actions" card to "Instructions" button
  - Keep the existing refresh button in bottom-right corner (avoid duplication)
  - Link instructions button to the new usage page when created
  - Update button styling and icon (fa-book or fa-question-circle)

- [x] **Streamer-focused BRB screen animation** ✨ *COMPLETED*
  - Timer tracking for break duration
  - Current time with dynamic timezone display
  - Rotating motivational messages with smooth transitions
  - Animated gradient background with breathing text effects
  - Designed for streamer's personal use rather than viewer-facing overlay

- [x] **Mascot easter egg functionality** ✨ *COMPLETED*
  - Add onclick listener to floating mascot for easter egg functionality (simple thank you message or interactive element)
  - Implemented modern popover API with thank you message and project info
  - Added close button (X) and click-outside-to-close functionality
  - Enhanced with hover effects and localStorage tracking for discovered easter egg
  - Includes subtle visual hints for undiscovered easter egg

- [x] **Add favicon to eliminate browser console errors** ✨ *COMPLETED*
  - Create or add favicon.ico to static/assets/ directory
  - Add favicon link tags to base template or all HTML templates
  - Eliminates "GET /favicon.ico 404" console errors during development
  - Improves professional appearance in browser tabs
  - Added OTA_favicon_round.png to all admin and main templates

- [x] **WebSocket architecture implementation** ✨ *COMPLETED*
- [x] **Video file support and Smart TV integration** ✨ *COMPLETED*
- [x] **Docker containerization with health checks** ✨ *COMPLETED*
- [x] **Admin frontend interface with file management** ✨ *COMPLETED*
- [x] **Page refresh functionality for seamless content switching** ✨ *COMPLETED*
- [x] **Status indicators and device tracking** ✨ *COMPLETED*
- [x] **Dark mode and Font Awesome icon integration** ✨ *COMPLETED*
- [x] **File structure organization (templates, static assets)** ✨ *COMPLETED*
- [x] **Global CSS design system with theme persistence** ✨ *COMPLETED*
- [x] **Professional admin interface styling and layout** ✨ *COMPLETED*
- [x] **Consistent header design across admin pages** ✨ *COMPLETED*
- [x] **Enhanced button styling and interactive elements** ✨ *COMPLETED*
- [x] **Scrollable containers for dynamic content (Connected Devices, Available Media)** ✨ *COMPLETED*
- [x] **Three-card layout restructuring for user management page** ✨ *COMPLETED*
- [x] **Current user recognition and highlighting in user lists** ✨ *COMPLETED*
- [x] **Blue highlight indicator for current user with proper CSS positioning** ✨ *COMPLETED*
- [x] **Welcome username display in header across all admin pages** ✨ *COMPLETED*
- [x] **Condensed social media buttons with icon-only design** ✨ *COMPLETED*
- [x] **Perfect height alignment for all header buttons (26px)** ✨ *COMPLETED*
- [x] **Security warnings for default credentials on first login** ✨ *COMPLETED*
- [x] **Login timestamp tracking for user activity monitoring** ✨ *COMPLETED*
- [x] **Add basic authentication for admin portal** ✨ *COMPLETED*
- [x] **Add user management page to admin interface** ✨ *COMPLETED*

- [x] **Port Configuration & Documentation Improvements** ✨ *COMPLETED*
  - Implemented dynamic port configuration with MAIN_PORT and WEBSOCKET_PORT variables
  - Updated Docker Compose files with proper port range mapping (8080-8081:8080-8081)
  - Enhanced startup messages to clearly indicate both Flask-SocketIO and raw WebSocket ports
  - Comprehensive documentation updates across README.md, DEVELOPMENT.md, and Docker files
  - Clarified distinction between Socket.IO (port 8080) and raw WebSocket (port 8081) endpoints
  - Added prominent port notes for user guidance on multi-port requirements

- [x] **Code Block UI/UX Enhancement** ✨ *COMPLETED*
  - Fixed code-header styling issues with proper flexbox alignment
  - Improved copy button positioning and visual hierarchy
  - Enhanced integration documentation with better code examples
  - Updated admin instruction pages with consistent code block formatting

- [x] **Refactor current HTML examples** ✨ *COMPLETED*
  - Created modular OTA integration system with external CSS/JS files (ota-integration.css, ota-integration.js)
  - Refactored test_anim1.html and test_brb.html to use external integration files
  - Implemented reusable WebSocket integration class with auto-initialization
  - Standardized overlay components with status indicators, connection handling, and page refresh
  - Enhanced code block styling and copy functionality for better user experience

- [x] **Docker Startup & Entrypoint Improvements** ✨ *COMPLETED*
  - Enhanced docker-entrypoint.sh with improved startup messages and port information
  - Added clear indication of both Flask-SocketIO (main port) and raw WebSocket ports
  - Improved Docker container initialization with better user feedback
  - Updated startup logging to show port configuration and service status

- [x] **Mobile Stream Control Interface** ✨ *COMPLETED* v0.8.5 → v0.8.6
  - Created dedicated mobile-optimized page for animation control during streams
  - Designed StreamDeck-style grid layout with thumbnail buttons and visual feedback
  - Implemented touch-friendly UI with large, easily tappable animation triggers
  - Added responsive design optimized for phone screens (portrait and landscape)
  - Included dual access routes (/mobile and /control) for easy bookmarking
  - Added haptic feedback and visual confirmation for successful animation triggers
  - Integrated real-time WebSocket status updates and viewer count display
  - Mobile interface includes stop all functionality and refresh capabilities