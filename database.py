import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), 'activity.db')

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Table to store discrete activity events
    # Each row is a small block of time (e.g., 5 seconds) 
    # where we capture what was actively being looked at and how many keys were typed.
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            app_name TEXT NOT NULL,
            window_title TEXT NOT NULL,
            keystrokes_count INTEGER DEFAULT 0,
            keystrokes_text TEXT DEFAULT ""
        )
    ''')
    
    # Table to store periodic screenshot paths
    c.execute('''
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def log_event(app_name, window_title, keystrokes_count, keystrokes_text):
    if not app_name: # Ignore complete nulls
        return
        
    conn = get_connection()
    c = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    c.execute('''
        INSERT INTO events (timestamp, app_name, window_title, keystrokes_count, keystrokes_text)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, app_name, window_title, keystrokes_count, keystrokes_text))
    
    conn.commit()
    conn.close()

def log_screenshot(file_path):
    conn = get_connection()
    c = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    c.execute('''
        INSERT INTO screenshots (timestamp, file_path)
        VALUES (?, ?)
    ''', (timestamp, file_path))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print(f"Database initialized at {DB_FILE}")
