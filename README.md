# Claude Session Monitor

A Python-based real-time monitoring tool for Claude Code Max Sessions usage, costs, and session limits. Displays a terminal-based dashboard with progress bars showing token consumption and time remaining in active sessions.

## Acknowledgments

This project is based on the work by [Daniel Roziecki](https://github.com/emssik/claude-session-monitor). Special thanks to Daniel for creating the concept and implementation that inspired this enhanced version.

**Original inspiration:** The initial idea comes from [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) by [Maciek-roboblog](https://github.com/Maciek-roboblog). Daniel's implementation built upon this concept, and this fork continues that evolution.

Thanks to both contributors for their innovative work in Claude API monitoring tools!

## Features

- **Real-time monitoring** of Claude Code Max Sessions
- **Token usage tracking** with progress bars and cost calculations
- **Session time remaining** with 5-hour window tracking
- **Cross-platform notifications** for time warnings and inactivity alerts
- **Monthly statistics** showing sessions used and remaining
- **Billing period tracking** with customizable start dates
- **Historical data** persistence and maximum usage tracking

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
   curl -O https://raw.githubusercontent.com/wjarka/claude-session-monitor/main/claude_monitor.py
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

