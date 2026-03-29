document.addEventListener('DOMContentLoaded', () => {
    const datePicker = document.getElementById('datePicker');
    const loadBtn = document.getElementById('loadBtn');
    
    // Set today as default
    const today = new Date().toISOString().split('T')[0];
    datePicker.value = today;
    
    loadBtn.addEventListener('click', () => loadData(datePicker.value));
    
    // Initial load
    loadData(today);
});

async function loadData(date) {
    try {
        const response = await fetch(`/api/daily?date=${date}`);
        const data = await response.json();
        
        renderDashboard(data.hours);
    } catch (error) {
        console.error('Failed to load data', error);
        document.getElementById('timeline').innerHTML = `<div class="empty-state" style="color: #ef4444;">Error loading data. Is the backend running?</div>`;
    }
}

function formatTime(seconds) {
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    const m = Math.floor(seconds / 60);
    const h = Math.floor(m / 60);
    if (h > 0) return `${h}h ${m % 60}m`;
    return `${m}m`;
}

function renderDashboard(hoursArr) {
    let totalSeconds = 0;
    let totalKeys = 0;
    let appTotals = {};
    
    const timelineEl = document.getElementById('timeline');
    const template = document.getElementById('timeline-template');
    
    timelineEl.innerHTML = '';
    
    if (!hoursArr || hoursArr.length === 0) {
        timelineEl.innerHTML = '<div class="empty-state">No activity tracked for this date yet.</div>';
        updateStats(0, 0, "-");
        return;
    }
    
    hoursArr.forEach((item) => {
        const h = item.Hour;
        const d = item.Data;
        
        // Accumulate daily stats
        totalSeconds += d.TotalActiveSeconds;
        totalKeys += d.TotalKeystrokes;
        
        for (const [app, sec] of Object.entries(d.Apps)) {
            appTotals[app] = (appTotals[app] || 0) + sec;
        }
        
        // Clone template
        const clone = template.content.cloneNode(true);
        const timeLabel = clone.querySelector('.time-label');
        const appsList = clone.querySelector('.apps-list');
        const windowsList = clone.querySelector('.windows-list ul');
        const keysPre = clone.querySelector('.keys-preview pre');
        
        timeLabel.textContent = `${h}:00`;
        
        // Populate card badges
        clone.querySelector('.time-badge').textContent = formatTime(d.TotalActiveSeconds);
        clone.querySelector('.keys-badge').textContent = `${d.TotalKeystrokes} keys`;
        
        // Populate Apps
        for (const [app, sec] of Object.entries(d.Apps)) {
            const row = document.createElement('div');
            row.className = 'app-row';
            row.innerHTML = `<span class="app-name">${escapeHtml(app)}</span><span class="app-time">${formatTime(sec)}</span>`;
            appsList.appendChild(row);
        }
        
        // Populate Windows
        if (d.WindowTitles && d.WindowTitles.length > 0) {
            d.WindowTitles.forEach(title => {
                const li = document.createElement('li');
                li.textContent = title;
                windowsList.appendChild(li);
            });
        } else {
            clone.querySelector('.windows-list').style.display = 'none';
        }
        
        // Populate Keys
        if (d.TextPreview && d.TextPreview.trim() !== '') {
            keysPre.textContent = d.TextPreview;
        } else {
            clone.querySelector('.keys-preview').style.display = 'none';
        }
        
        timelineEl.appendChild(clone);
    });
    
    // Find top app
    let topApp = "-";
    let topAppSecs = 0;
    for (const [app, sec] of Object.entries(appTotals)) {
        if (sec > topAppSecs) {
            topAppSecs = sec;
            topApp = app;
        }
    }
    
    updateStats(totalSeconds, totalKeys, topApp);
}

function updateStats(secs, keys, app) {
    document.getElementById('totalTime').textContent = formatTime(secs);
    document.getElementById('totalKeys').textContent = keys.toLocaleString();
    document.getElementById('topApp').textContent = escapeHtml(app);
}

function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
         .toString()
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
