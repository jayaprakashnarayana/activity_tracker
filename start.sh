#!/bin/bash
# start.sh
# Navigate to the correct directory and activate environment
cd "$(dirname "$0")"
source venv/bin/activate

# Check and start tracker
if pgrep -f "python3 tracker.py" > /dev/null; then
    echo "✅ Tracker daemon is already running."
else
    echo "🚀 Starting Tracker daemon in the background..."
    nohup python3 tracker.py > tracker.log 2>&1 &
fi

# Check and start server
if pgrep -f "python3 app.py" > /dev/null; then
    echo "✅ Dashboard Server is already running."
else
    echo "🚀 Starting Dashboard Server in the background..."
    nohup python3 app.py > app.log 2>&1 &
fi

echo ""
echo "🎉 Activity Tracker is now fully running in the background!"
echo "You can access your dashboard at: http://127.0.0.1:5001"
echo "You can safely close this terminal window."
