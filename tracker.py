import time
import subprocess
import threading
from pynput import keyboard
from database import init_db, log_event

# Global variables to store typing stats in the current interval
current_keys_typed = []
keys_lock = threading.Lock()

def on_press(key):
    global current_keys_typed
    with keys_lock:
        try:
            # Store alphanumeric keys directly
            if key.char is not None:
                current_keys_typed.append(key.char)
        except AttributeError:
            # Store special keys
            if key == keyboard.Key.space:
                current_keys_typed.append(" ")
            elif key == keyboard.Key.enter:
                current_keys_typed.append("\n")
            elif key == keyboard.Key.tab:
                current_keys_typed.append("\t")
            elif key == keyboard.Key.backspace:
                current_keys_typed.append("[BS]")
            else:
                # We can ignore other control keys to keep the log relatively clean
                pass

def get_active_window_info():
    script = """
    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        set appName to name of frontApp
        try
            set windowTitle to name of front window of frontApp
        on error
            set windowTitle to "Unknown"
        end try
        return appName & "|||" & windowTitle
    end tell
    """
    try:
        # We use strict check_output timeout to avoid hangs
        output = subprocess.check_output(['osascript', '-e', script], timeout=2)
        decoded = output.decode('utf-8').strip()
        parts = decoded.split('|||')
        app_name = parts[0]
        window_title = parts[1] if len(parts) > 1 else ""
        return app_name, window_title
    except Exception as e:
        return None, None

def tracking_loop():
    global current_keys_typed
    
    interval = 5  # Log an event every 5 seconds
    print(f"Starting tracking loop. Logging every {interval} seconds...")
    
    while True:
        time.sleep(interval)
        
        app_name, window_title = get_active_window_info()
        
        with keys_lock:
            # Safely grab the keystrokes and clear the buffer
            keys_text = "".join(current_keys_typed)
            keys_count = len(current_keys_typed)
            current_keys_typed = []
            
        if app_name is not None:
            log_event(app_name, window_title, keys_count, keys_text)

if __name__ == '__main__':
    # Initialize DB (creates table if not exists)
    init_db()
    
    # Start the keylogger in a background thread
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    # Start the tracking loop on the main thread
    try:
        tracking_loop()
    except KeyboardInterrupt:
        print("Stopping tracker...")
        listener.stop()
