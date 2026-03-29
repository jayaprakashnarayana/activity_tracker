from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static', static_url_path='/')

DB_FILE = os.path.join(os.path.dirname(__file__), 'activity.db')

def get_connection():
    return sqlite3.connect(DB_FILE)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/daily')
def get_daily_summary():
    # Expects format YYYY-MM-DD
    target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_connection()
    c = conn.cursor()
    
    # Get all events for the target day
    # Events are logged every 5 seconds.
    c.execute('''
        SELECT timestamp, app_name, window_title, keystrokes_count, keystrokes_text
        FROM events
        WHERE timestamp LIKE ?
        ORDER BY timestamp ASC
    ''', (target_date + "%",))
    
    rows = c.fetchall()
    conn.close()

    # We want to group by hour
    # Output structure: 
    # hourly: { "00": { apps: { "Chrome": seconds }, keys: total_keys, text_preview: "" } ... }
    
    hourly_data = {}
    
    # Initialize all 24 hours
    for h in range(24):
        h_str = f"{h:02d}"
        hourly_data[h_str] = {
            "TotalActiveSeconds": 0,
            "TotalKeystrokes": 0,
            "Apps": {},
            "WindowTitles": [], # list of unique or longest window titles
            "TextPreview": ""  # preview of what was typed
        }
        
    for row in rows:
        timestamp, app_name, window_title, keystrokes_count, text = row
        
        # parse timestamp (e.g. 2026-03-29T14:19:47.12345)
        try:
            time_obj = datetime.fromisoformat(timestamp)
        except ValueError:
            continue
            
        h_str = f"{time_obj.hour:02d}"
        
        # Add 5 seconds of active time per event (since tracking loop is 5s)
        hourly_data[h_str]["TotalActiveSeconds"] += 5
        hourly_data[h_str]["TotalKeystrokes"] += keystrokes_count
        if text:
             # Limit the text preview size to not send massive payloads
             if len(hourly_data[h_str]["TextPreview"]) < 500:
                hourly_data[h_str]["TextPreview"] += text
             
        if app_name not in hourly_data[h_str]["Apps"]:
            hourly_data[h_str]["Apps"][app_name] = 0
            
        hourly_data[h_str]["Apps"][app_name] += 5
        
        # Add window title if unique to summarize roughly what they did
        if window_title and window_title not in hourly_data[h_str]["WindowTitles"] and len(hourly_data[h_str]["WindowTitles"]) < 10:
            if window_title != "Unknown":
                hourly_data[h_str]["WindowTitles"].append(window_title)

    # Convert mapping to list for easier rendering
    summary_list = []
    for h in range(24):
        h_str = f"{h:02d}"
        data = hourly_data[h_str]
        
        if data["TotalActiveSeconds"] > 0:
            # Sort apps descending by time
            sorted_apps = dict(sorted(data["Apps"].items(), key=lambda item: item[1], reverse=True))
            data["Apps"] = sorted_apps
            
            summary_list.append({
                "Hour": h_str,
                "Data": data
            })
            
    return jsonify({
        "date": target_date,
        "hours": summary_list
    })

if __name__ == '__main__':
    # Ensure static directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static'), exist_ok=True)
    app.run(port=5001, debug=True)
