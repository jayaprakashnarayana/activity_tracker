from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import os
import shutil
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
            "WindowTitles": [], # list of {title, url}
            "TextPreview": "",  # preview of what was typed
            "Screenshots": []
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
        if window_title and window_title != "Unknown":
            parsed_title = window_title
            parsed_url = ""
            if " [URL_SEP] " in window_title:
                parts = window_title.split(" [URL_SEP] ")
                parsed_title = parts[0]
                parsed_url = parts[1] if len(parts) > 1 else ""

            # Check uniqueness based on title
            exists = any(item.get("title") == parsed_title for item in hourly_data[h_str]["WindowTitles"])
            
            if not exists and len(hourly_data[h_str]["WindowTitles"]) < 10:
                hourly_data[h_str]["WindowTitles"].append({
                    "title": parsed_title,
                    "url": parsed_url
                })

    # Fetch screenshots for the day
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT timestamp, file_path
        FROM screenshots
        WHERE timestamp LIKE ?
        ORDER BY timestamp ASC
    ''', (target_date + "%",))
    
    ss_rows = c.fetchall()
    conn.close()
    
    for row in ss_rows:
        ss_timestamp, ss_path = row
        try:
            time_obj = datetime.fromisoformat(ss_timestamp)
        except ValueError:
            continue
        h_str = f"{time_obj.hour:02d}"
        hourly_data[h_str]["Screenshots"].append(ss_path)

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

@app.route('/api/storage_stats')
def get_storage_stats():
    # Calculate size of screenshots folder
    ss_dir = os.path.join(os.path.dirname(__file__), 'static', 'screenshots')
    total_size = 0
    file_count = 0
    if os.path.exists(ss_dir):
        for f in os.listdir(ss_dir):
            fp = os.path.join(ss_dir, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
                file_count += 1
                
    # return mb
    return jsonify({
        "size_mb": round(total_size / (1024 * 1024), 2),
        "file_count": file_count
    })

@app.route('/api/cleanup_screenshots', methods=['POST'])
def cleanup_screenshots():
    # expects JSON { "days": 7 | 30 | -1 (all) }
    req = request.get_json() or {}
    days = req.get("days", -1)
    
    ss_dir = os.path.join(os.path.dirname(__file__), 'static', 'screenshots')
    if not os.path.exists(ss_dir):
        return jsonify({"success": True, "deleted": 0})
        
    deleted_count = 0
    now = time.time() if hasattr(os, 'stat') else 0
    import time # Ensure time is available locally to avoid circulars
    
    cutoff = time.time() - (days * 86400) if days > 0 else float('inf')
    
    for f in os.listdir(ss_dir):
        fp = os.path.join(ss_dir, f)
        if os.path.isfile(fp):
            # If "all", delete everything
            if days == -1:
                os.remove(fp)
                deleted_count += 1
            else:
                # Delete if older than cutoff
                if os.stat(fp).st_mtime < cutoff:
                    os.remove(fp)
                    deleted_count += 1
                    
    # We could also purge db references here, but for now orphaned DB records won't break the frontend.
    
    return jsonify({"success": True, "deleted": deleted_count})

if __name__ == '__main__':
    # Ensure static directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static', 'screenshots'), exist_ok=True)
    app.run(port=5001, debug=True)
