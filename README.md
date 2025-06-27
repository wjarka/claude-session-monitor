# Claude Session Monitor

A Python-based real-time monitoring tool for Claude API token usage, costs, and session limits. Displays a terminal-based dashboard with progress bars showing token consumption and time remaining in active sessions.

**Inspired by:** [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) - I liked the concept but needed a different technical implementation, so I created my own version.

## Requirements

- **macOS** (optimized for macOS notifications, but runs on other platforms)
- **Python 3.9+** (uses `zoneinfo` from standard library)
- **ccusage CLI tool** - Required for fetching Claude API usage data

## Installation

1. **Install ccusage** following the instructions at: https://github.com/ryoppippi/ccusage
2. **Download the script:**
   ```bash
   curl -O https://raw.githubusercontent.com/USER/claude-session-monitor/main/claude_monitor.py
   ```
3. **Run the monitor:**
   ```bash
   python3 claude_monitor.py
   ```

## What It Shows

The monitor displays:
- **Current tokens used** in active sessions
- **Maximum tokens reached** during the billing period  
- **Percentage of monthly limit utilized**
- **Real-time session tracking** with time remaining
- **Cost tracking** for current and maximum usage
- **macOS notifications** for time warnings and inactivity alerts

## Usage and Options

```bash
python3 claude_monitor.py --help
usage: claude_monitor.py [-h] [--start-day START_DAY] [--recalculate] [--test-alert] [--version]

Claude Session Monitor - Monitor Claude API token and cost usage.

options:
  -h, --help            show this help message and exit
  --start-day START_DAY
                        Day of the month the billing period starts.
  --recalculate         Forces re-scanning of history to update 
                        stored values (max tokens and costs).
  --test-alert          Sends a test system notification (macOS only) and exits.
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

# Test notifications (macOS only)
python3 claude_monitor.py --test-alert
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
- `LOCAL_TZ = ZoneInfo("Europe/Warsaw")` - Display timezone

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