document.addEventListener('DOMContentLoaded', () => {
    const datePicker = document.getElementById('datePicker');
    const loadBtn = document.getElementById('loadBtn');
    
    // Set today as default
    const today = new Date().toISOString().split('T')[0];
    datePicker.value = today;
    
    loadBtn.addEventListener('click', () => loadData(datePicker.value));
    
    // Initial load
    loadData(today);
    
    // Settings logic
    document.getElementById('settingsBtn').addEventListener('click', openSettings);
    document.getElementById('closeSettings').addEventListener('click', () => {
        document.getElementById('settingsModal').classList.remove('active');
    });
});

async function openSettings() {
    document.getElementById('settingsModal').classList.add('active');
    try {
        const res = await fetch('/api/storage_stats');
        const data = await res.json();
        document.getElementById('storageSize').textContent = `${data.size_mb} MB`;
        document.getElementById('storageCount').textContent = data.file_count;
    } catch (e) {
        console.error(e);
        document.getElementById('storageSize').textContent = "Error";
    }
}

async function cleanupScreenshots(days) {
    if (confirm("Are you sure you want to delete these screenshots? This cannot be undone.")) {
        try {
            const res = await fetch('/api/cleanup_screenshots', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ days: days })
            });
            const data = await res.json();
            alert(`Successfully deleted ${data.deleted} screenshots.`);
            openSettings(); // refresh stats
            loadData(document.getElementById('datePicker').value); // refresh UI
        } catch (e) {
            alert("Error running cleanup.");
        }
    }
}

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
        const gallery = clone.querySelector('.screenshot-gallery');
        
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
        
        // Populate Windows & URLs
        if (d.WindowTitles && d.WindowTitles.length > 0) {
            d.WindowTitles.forEach(item => {
                const li = document.createElement('li');
                // handle either new separated dict or old string format
                if (typeof item === 'string') {
                    li.textContent = item;
                } else {
                    li.textContent = item.title;
                    if (item.url && item.url.startsWith('http')) {
                        const a = document.createElement('a');
                        a.href = item.url;
                        a.target = '_blank';
                        a.className = 'window-link';
                        a.textContent = 'Open Link ↗';
                        li.appendChild(a);
                    }
                }
                windowsList.appendChild(li);
            });
        } else {
            clone.querySelector('.windows-list').style.display = 'none';
        }
        
        // Populate Screenshots
        if (d.Screenshots && d.Screenshots.length > 0) {
            d.Screenshots.forEach(path => {
                const img = document.createElement('img');
                img.src = `/${path}`; // points to static root
                // clicking image opens it full screen
                img.onclick = () => window.open(img.src, '_blank');
                gallery.appendChild(img);
            });
        } else {
            gallery.style.display = 'none';
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
