# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Claude API token usage monitor that provides real-time tracking of token consumption, costs, and session limits. The tool displays a terminal-based dashboard showing progress bars for token usage and time remaining in active sessions.

## Architecture

- **Core Module**: `claude_monitor.py` - Main monitoring script with real-time display
- **Localized Version**: `claude_monitor.org.py` - Polish language variant
- **External Dependency**: Requires `ccusage` CLI tool for fetching Claude API usage data

### Key Components

1. **Configuration Management**: Stores user settings and historical data in `~/.config/claude-monitor/config.json`
2. **Data Fetching**: Integrates with `ccusage` command-line tool to retrieve usage blocks
3. **Real-time Monitoring**: Tracks active sessions and updates display every second
4. **Notification System**: Cross-platform notifications for time warnings and inactivity alerts
5. **Billing Period Tracking**: Calculates usage against monthly subscription limits

## Development Commands

No specific build, test, or lint commands are defined in the project configuration. The scripts are standalone Python executables.

### Running the Monitor

```bash
# Basic usage
python3 claude_monitor.py

# With custom billing start day
python3 claude_monitor.py --start-day 15

# Force recalculation of historical data
python3 claude_monitor.py --recalculate

# Test notifications (cross-platform)
python3 claude_monitor.py --test-alert
```

## Dependencies

- **System Requirement**: `ccusage` CLI tool must be installed and accessible in PATH
- **Python**: Requires Python 3.9+ (uses `zoneinfo` from standard library)
- **Platform**: Cross-platform support for macOS, Linux (including Arch Linux with Hyprland), and Windows

## Configuration Constants

Key configurable values in the source code:
- `TOTAL_MONTHLY_SESSIONS = 50` - Expected monthly session limit
- `TIME_REMAINING_ALERT_MINUTES = 30` - Warning threshold for session end
- `INACTIVITY_ALERT_MINUTES = 10` - Notification for idle periods
- `LOCAL_TZ = ZoneInfo("Europe/Warsaw")` - Display timezone

## Data Flow

1. Fetches current usage data from `ccusage blocks -j`
2. Maintains local cache with 10-second refresh intervals
3. Tracks active sessions by comparing current time with session time ranges
4. Updates monthly statistics when sessions end
5. Persists configuration and historical maximums to JSON file