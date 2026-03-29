# macOS Activity Tracker & Hourly Summarizer ⏳

A local, privacy-focused application for macOS that tracks your active applications, window titles, and keystrokes throughout the day, presenting them in a beautiful hourly timeline on a modern web dashboard.

## 🚀 Features
- **Keylogging & App Tracking**: Automatically logs what apps you are using, what window or website is active, and the keystrokes typed.
- **Hourly Breakdowns**: Groups your activity into 1-hour chunks.
- **Local Dashboard**: A modern, dark-themed UI (glassmorphism design) to review your daily stats.
- **Privacy First**: All data is saved strictly to a local SQLite database (`activity.db`). The `.gitignore` ensures this private data is never pushed to GitHub.

## 🛠 Prerequisites
- macOS
- Python 3.x
- Terminal / iTerm2

## 📦 Installation

To get the application running on your local machine, open your Mac's Terminal and run the following commands:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jayaprakashnarayana/activity_tracker.git
   cd activity_tracker
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the required dependencies:**
   ```bash
   pip install pynput Flask pyobjc-framework-Cocoa
   ```

## 🎮 How to Use

The application is split into two parts: the background tracker daemon and the web dashboard server. You should run both simultaneously in separate terminal windows.

### 1. Start the Background Tracker
In your first Terminal window (with your virtual environment activated):
```bash
python3 tracker.py
```

> **⚠️ macOS Permissions Warning:**
> The first time you run this, macOS will block the script from reading your keystrokes and window titles due to security protections.
> You must go to **System Settings > Privacy & Security > Accessibility** and explicitly enable your Terminal app (or IDE). Once enabled, restart the `tracker.py` script.

### 2. Start the Dashboard Server
Open a **new** Terminal window, activate the environment, and run the server:
```bash
cd activity_tracker
source venv/bin/activate
python3 app.py
```

### 3. View Your Timeline
Open your preferred web browser and go to:
**http://127.0.0.1:5001**

You will see your application usage, time spent, window titles, and key logs populating in real-time as you use your machine!

## 🔒 Security Note
Do **NOT** remove `activity.db` from your `.gitignore`. This database tracks exact alphanumeric keystrokes, which can include sensitive information if typed outside of secure password fields. Keep this repository private and secure.
