#!/bin/bash
# stop.sh
echo "🛑 Stopping Activity Tracker and Dashboard..."

# Kill the specific python processes matching our scripts
pkill -f "python3 tracker.py"
if [ $? -eq 0 ]; then
    echo "✅ Tracker daemon stopped."
else
    echo "Tracker daemon was not running."
fi

pkill -f "python3 app.py"
if [ $? -eq 0 ]; then
    echo "✅ Dashboard Server stopped."
else
    echo "Dashboard Server was not running."
fi

echo "All Activity Tracker processes successfully closed."
