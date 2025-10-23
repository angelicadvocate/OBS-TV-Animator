import os
import time
from threading import Thread
from app import socketio, load_state, save_state, find_media_file

class TriggerFileWatcher:
    def __init__(self, trigger_file_path):
        self.trigger_file_path = trigger_file_path
        self.last_modified = 0
        self.running = True
        
    def start_watching(self):
        """Start watching the trigger file in a background thread"""
        thread = Thread(target=self._watch_file)
        thread.daemon = True
        thread.start()
        print(f"Started watching trigger file: {self.trigger_file_path}")
        
    def _watch_file(self):
        """Watch for changes to the trigger file"""
        while self.running:
            try:
                if os.path.exists(self.trigger_file_path):
                    current_modified = os.path.getmtime(self.trigger_file_path)
                    
                    if current_modified > self.last_modified:
                        self.last_modified = current_modified
                        
                        # Read the animation name from the file
                        with open(self.trigger_file_path, 'r') as f:
                            animation_name = f.read().strip()
                            
                        if animation_name:
                            print(f"Trigger file changed: {animation_name}")
                            self._handle_trigger(animation_name)
                            
                        # Delete the file after processing
                        os.remove(self.trigger_file_path)
                        
            except Exception as e:
                print(f"Error watching trigger file: {e}")
                
            time.sleep(0.5)  # Check every 500ms
            
    def _handle_trigger(self, animation_name):
        """Handle the animation trigger"""
        try:
            # Validate that the media file exists
            media_path, media_type = find_media_file(animation_name)
            if not media_path:
                print(f"Media file '{animation_name}' not found")
                return
                
            # Update state
            state = load_state()
            state['current_animation'] = animation_name
            save_state(state)

            # Emit animation change to all clients
            socketio.emit('animation_changed', {
                'current_animation': animation_name,
                'media_type': media_type,
                'message': f"Media changed to '{animation_name}' ({media_type}) via file trigger",
                'refresh_page': True
            })

            # Emit explicit page refresh
            socketio.emit('page_refresh', {
                'reason': 'file_trigger',
                'new_media': animation_name,
                'media_type': media_type
            })

            print(f"Successfully triggered animation: {animation_name}")
            
        except Exception as e:
            print(f"Error handling trigger: {e}")
            
    def stop_watching(self):
        """Stop watching the trigger file"""
        self.running = False

# Example usage - add this to your app.py
if __name__ == "__main__":
    trigger_file = os.path.join(os.path.dirname(__file__), "data", "trigger.txt")
    watcher = TriggerFileWatcher(trigger_file)
    watcher.start_watching()
    
    # Your Flask app would run here
    # The file watcher runs in the background