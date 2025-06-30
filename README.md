# Claude Session Monitor

**Code Authors:** Gemini 2.5 Pro & Claude Code
**Human Role:** Screenshots + Requirements

As a human, I don't know what the code looks like and I'm completely not interested in it. The tool should simply do what I need. This is also a "state of mind" that one needs to mature to ;)

## History

https://www.linkedin.com/posts/daniel-roziecki-znajomy-powiedzia%C5%82-mi-%C5%BCe-do-tego-trzeba-activity-7343537196462714881-tFat (PL Only)

A friend told me that you need the right mindset for this, and I think he's right.

3 days ago, someone shared a link to a cool app on GitHub (Claude Token Monitor). While I really liked the idea itself, it turned out that its operating philosophy wasn't the best for me + I was missing certain information.

So... I took a screenshot. I fired up Gemini 2.5 Pro.

I uploaded the image, described what the app does and what I wanted it to do, and after 30 minutes, after a few iterations, I have a working script that does exactly what I need.

It shows me how many sessions are left until the end of the subscription, how much money I would spend on tokens if I didn't have the Max subscription, how much time is left until the end of the actual 5-hour window (because that's how the Max subscription works - you have 50 five-hour sessions per month). It sends me notifications 30 minutes before the window ends and when nothing happens for 10 minutes (after all, it has to pay for itself :) ).

And these are all elements that the original app didn't have.

So I took a great idea and with a model (based on a screenshot and my description) in 30 minutes, 100% customized it for myself.

Yes, such things are no longer just in the Era ;)

Don't be afraid, experiment, keep an open mind and have fun with it.

## Overview

A Python-based real-time monitoring tool for Claude Code Max Sessions usage, costs, and session limits. Displays a terminal-based dashboard with progress bars showing token consumption and time remaining in active sessions.

**Inspired by:** [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) - I liked the concept but needed a different technical implementation, so I created my own version.

## Requirements

- **Cross-platform support:** macOS, Linux (including Arch Linux with Hyprland), and Windows
- **Python 3.9+** (uses `zoneinfo` from standard library)
- **ccusage CLI tool** - Required for fetching Claude API usage data

## Installation

1. **Install ccusage** following the instructions at: https://github.com/ryoppippi/ccusage

2. **Set up Python virtual environment (recommended):**
   ```bash
   python3 -m venv claude-monitor-env
   source claude-monitor-env/bin/activate  # On Windows: claude-monitor-env\Scripts\activate
   ```

3. **Install required Python packages:**
   ```bash
   pip install zoneinfo  # Only needed if Python < 3.9
   ```
   Note: The script uses only standard library modules for Python 3.9+, so no additional packages are required for modern Python versions.

   **Cross-platform Notifications:**
   
   - **macOS:** Uses `terminal-notifier` (if installed) or falls back to `osascript`
     ```bash
     brew install terminal-notifier  # Optional, for enhanced notifications
     ```
   
   - **Linux:** Uses `notify-send` (libnotify) or `dunstify` (dunst notifications)
     ```bash
     # Arch Linux / Arch-based distributions
     sudo pacman -S libnotify          # For notify-send
     sudo pacman -S dunst              # For dunstify (recommended for Hyprland)
     
     # Ubuntu/Debian
     sudo apt install libnotify-bin    # For notify-send
     sudo apt install dunst            # For dunstify
     
     # Fedora
     sudo dnf install libnotify        # For notify-send
     sudo dnf install dunst            # For dunstify
     ```
   
   - **Windows:** Uses PowerShell toast notifications (built-in)
   
   If no notification system is available, the monitor continues working without notifications.

4. **Download the script:**
   ```bash
   curl -O https://raw.githubusercontent.com/emssik/claude-session-monitor/main/claude_monitor.py
   ```

5. **Run the monitor:**
   ```bash
   python3 claude_monitor.py --start-day 15
   ```

## What It Shows

The monitor displays:
- **Current tokens used** in active sessions
- **Maximum tokens reached** during the billing period
- **Percentage of monthly limit utilized**
- **Real-time session tracking** with time remaining
- **Cost tracking** for current and maximum usage
- **Cross-platform notifications** for time warnings and inactivity alerts

## Usage and Options

```bash
python3 claude_monitor.py --help
usage: claude_monitor.py [-h] [--start-day START_DAY] [--recalculate] [--test-alert] [--timezone TIMEZONE] [--version]

Claude Session Monitor - Monitor Claude API token and cost usage.

options:
  -h, --help            show this help message and exit
  --start-day START_DAY
                        Day of the month the billing period starts.
  --recalculate         Forces re-scanning of history to update
                        stored values (max tokens and costs).
  --test-alert          Sends a test system notification and exits.
  --timezone TIMEZONE   Timezone for display (e.g., 'America/New_York', 'UTC', 'Asia/Tokyo'). Default: Europe/Warsaw
  --version             Show version information and exit.
```

### Examples

```bash
# Basic usage
python3 claude_monitor.py

# Custom billing start day (15th of each month)
python3 claude_monitor.py --start-day 15

# Force recalculation of historical data
python3 claude_monitor.py --recalculate

# Test notifications (cross-platform)
python3 claude_monitor.py --test-alert

# Use different timezone (default is Europe/Warsaw)
python3 claude_monitor.py --timezone UTC
python3 claude_monitor.py --timezone America/New_York
python3 claude_monitor.py --timezone Asia/Tokyo
```

## Linux Setup (Arch Linux + Hyprland)

For optimal experience on Arch Linux with Hyprland, follow these additional steps:

### 1. Install Dependencies
```bash
# Install ccusage (required)
# Follow instructions at: https://github.com/ryoppippi/ccusage

# Install notification support (recommended)
sudo pacman -S libnotify dunst

# Optional: Install a notification daemon if not already running
# Dunst is recommended for Hyprland
sudo pacman -S dunst
```

### 2. Configure Dunst for Hyprland (Optional)
If you want to customize notifications, create a dunst config:
```bash
mkdir -p ~/.config/dunst
cp /etc/dunst/dunstrc ~/.config/dunst/
```

Edit `~/.config/dunst/dunstrc` to customize notification appearance and behavior.

### 3. Test Notifications
```bash
# Test the notification system
python3 claude_monitor.py --test-alert

# If notifications don't appear, check if a notification daemon is running:
pgrep -x dunst || pgrep -x mako

# Start dunst if needed:
dunst &
```

### 4. Auto-start (Optional)
To start the monitor automatically with Hyprland, add to your `~/.config/hypr/hyprland.conf`:
```bash
exec-once = cd /path/to/claude-monitor && python3 claude_monitor.py
```

## Configuration

The tool automatically creates and manages configuration in `~/.config/claude-monitor/config.json`. This file stores:

- Historical maximum token and cost values
- User preferences (billing start day)
- Session tracking data
- Alert settings

### Key Configuration Constants

You can modify these values in the source code:

- `TOTAL_MONTHLY_SESSIONS = 50` - Expected monthly session limit
- `TIME_REMAINING_ALERT_MINUTES = 30` - Warning threshold for session end
- `INACTIVITY_ALERT_MINUTES = 10` - Notification for idle periods
- `LOCAL_TZ = ZoneInfo("Europe/Warsaw")` - Default display timezone (can be overridden with --timezone)

## How It Works

1. **Data Fetching**: Integrates with `ccusage blocks -j` to retrieve usage data
2. **Local Caching**: Maintains cache with 10-second refresh intervals
3. **Session Tracking**: Monitors active sessions by comparing current time with session ranges
4. **Statistics**: Updates monthly statistics when sessions end
5. **Persistence**: Saves configuration and historical maximums to JSON file

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Inspired by [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) by Maciek-roboblog.
