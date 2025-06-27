#!/usr/bin/env python3
import os
import sys
import json
import time
import shutil
import subprocess
import argparse
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

# --- Configuration Singleton ---
class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Default configuration
        self.VERSION = "1.0.0"
        self.TOTAL_MONTHLY_SESSIONS = 50
        self.REFRESH_INTERVAL_SECONDS = 1
        self.CCUSAGE_FETCH_INTERVAL_SECONDS = 10
        self.CONFIG_DIR = os.path.expanduser("~/.config/claude-monitor")
        self.CONFIG_FILE = os.path.join(self.CONFIG_DIR, "config.json")
        
        # Alert Configuration (macOS only)
        self.TIME_REMAINING_ALERT_MINUTES = 30
        self.INACTIVITY_ALERT_MINUTES = 10
        
        # Time Zones
        self.UTC_TZ = ZoneInfo("UTC")
        self.LOCAL_TZ = ZoneInfo("Europe/Warsaw")
        
        self._initialized = True
    
    @classmethod
    def instance(cls):
        return cls()
    
    def set_timezone(self, timezone_str):
        """Set the local timezone"""
        self.LOCAL_TZ = ZoneInfo(timezone_str)

# --- ANSI Colors ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# --- Helper Functions ---

def show_macos_notification(title, message):
    if sys.platform != "darwin": return
    if shutil.which("terminal-notifier"):
        try:
            command = ["terminal-notifier", "-title", title, "-message", message, "-sound", "default"]
            subprocess.run(command, check=True, capture_output=True, text=True)
            return
        except (subprocess.CalledProcessError, FileNotFoundError): pass
    else:
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError): pass

def clear_screen_for_refresh():
    print("\033[H\033[J\033[?25l", end="")

def parse_utc_time(time_str: str) -> datetime:
    config = Config.instance()
    time_str = time_str.split('.')[0]
    return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=config.UTC_TZ)

def save_config(data: dict):
    config = Config.instance()
    try:
        os.makedirs(config.CONFIG_DIR, exist_ok=True)
        with open(config.CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError: pass

def load_config() -> dict:
    config = Config.instance()
    if not os.path.exists(config.CONFIG_FILE): return {}
    try:
        with open(config.CONFIG_FILE, 'r') as f: return json.load(f)
    except (IOError, json.JSONDecodeError): return {}

def run_ccusage(since_date: str = None) -> dict:
    command = ["ccusage", "blocks", "-j"]
    if since_date: command.extend(["-s", since_date])
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
        return {"blocks": []}

def get_subscription_period_start(start_day: int) -> date:
    today = date.today()
    if today.day >= start_day:
        return today.replace(day=start_day)
    else:
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        return last_day_of_previous_month.replace(day=min(start_day, last_day_of_previous_month.day))

def get_next_renewal_date(start_day: int) -> date:
    """Oblicza datę następnego odnowienia abonamentu."""
    today = date.today()
    # Jeśli jesteśmy już po dniu odnowienia w tym miesiącu...
    if today.day >= start_day:
        # ...następne odnowienie jest w przyszłym miesiącu.
        next_month = today.month + 1
        next_year = today.year
        if next_month > 12:
            next_month = 1
            next_year += 1
    # Jeśli jesteśmy jeszcze przed dniem odnowienia...
    else:
        # ...następne odnowienie jest w tym miesiącu.
        next_month = today.month
        next_year = today.year
    return date(next_year, next_month, start_day)

def create_progress_bar(percentage: float, width: int = 40) -> str:
    filled_width = int(width * percentage / 100)
    bar = '█' * filled_width + ' ' * (width - filled_width)
    return f"[{bar}]"

def format_timedelta(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes:02d}m"

def main(args):
    os.system('cls' if os.name == 'nt' else 'clear')
    config = load_config()
    
    # Smart single data fetch - determine optimal date range
    sub_start_date = get_subscription_period_start(args.start_day)
    sub_start_date_str = sub_start_date.strftime('%Y-%m-%d')
    
    # Determine what data we need
    need_full_rescan = args.recalculate
    need_max_tokens = not config.get("max_tokens") or args.recalculate
    need_monthly_recalc = args.recalculate or config.get("monthly_meta", {}).get("period_start") != sub_start_date_str
    
    if need_full_rescan:
        print(f"{Colors.WARNING}Full recalculation - fetching all data...{Colors.ENDC}")
        fetch_since = None  # Get everything
    elif need_monthly_recalc:
        print(f"{Colors.WARNING}New billing period - fetching data from {sub_start_date_str}...{Colors.ENDC}")
        fetch_since = sub_start_date.strftime('%Y%m%d')
    else:
        # Incremental: get data from last week to catch any new sessions
        last_check = config.get("last_incremental_update")
        if last_check:
            since_date = datetime.strptime(last_check, '%Y-%m-%d') - timedelta(days=2)
        else:
            since_date = datetime.now() - timedelta(days=7)
        fetch_since = since_date.strftime('%Y%m%d')
        print(f"{Colors.CYAN}Incremental update from {since_date.strftime('%Y-%m-%d')}...{Colors.ENDC}")
    
    # Single ccusage call!
    data = run_ccusage(fetch_since)
    if not data or "blocks" not in data:
        print(f"{Colors.FAIL}Failed to fetch usage data{Colors.ENDC}")
        return
    
    blocks = data["blocks"]
    
    # Process max tokens
    max_tokens_so_far = config.get("max_tokens", 35000)
    if need_max_tokens:
        all_tokens = [b.get("totalTokens", 0) for b in blocks if not b.get("isGap", False)]
        if all_tokens:
            new_max = max(all_tokens)
            if new_max > max_tokens_so_far:
                max_tokens_so_far = new_max
                config["max_tokens"] = max_tokens_so_far
                config["last_max_tokens_scan"] = datetime.now().strftime('%Y-%m-%d')
                print(f"{Colors.GREEN}New maximum found: {max_tokens_so_far:,} tokens.{Colors.ENDC}")
    else:
        # Check recent data for new max
        recent_tokens = [b.get("totalTokens", 0) for b in blocks if not b.get("isGap", False)]
        if recent_tokens:
            recent_max = max(recent_tokens)
            if recent_max > max_tokens_so_far:
                max_tokens_so_far = recent_max
                config["max_tokens"] = max_tokens_so_far
                print(f"{Colors.GREEN}New maximum found: {max_tokens_so_far:,} tokens.{Colors.ENDC}")
    
    # Process monthly data
    monthly_meta = config.get("monthly_meta", {})
    processed_sessions = config.get("processed_sessions", [])
    
    if need_monthly_recalc:
        # Full monthly recalculation - filter blocks by billing period
        period_start_utc = parse_utc_time(sub_start_date_str + "T00:00:00")
        period_blocks = [b for b in blocks 
                        if not b.get("isGap", False) and 
                        parse_utc_time(b["startTime"]) >= period_start_utc]
        completed_blocks = [b for b in period_blocks if not b.get("isActive", False)]
        
        sessions_used = len(completed_blocks)
        cost_this_month = sum(b.get("costUSD", 0) for b in completed_blocks)
        processed_sessions = [b["id"] for b in completed_blocks]
        
        monthly_meta = {"period_start": sub_start_date_str, "cost": cost_this_month, "sessions": sessions_used}
        config["monthly_meta"] = monthly_meta
        config["processed_sessions"] = processed_sessions
    else:
        # Incremental update: process only new sessions within billing period
        period_start_utc = parse_utc_time(sub_start_date_str + "T00:00:00")
        new_sessions_found = 0
        for block in blocks:
            if (block.get("isGap", False) or 
                block["id"] in processed_sessions or
                parse_utc_time(block["startTime"]) < period_start_utc):
                continue
            
            # Only process completed sessions (not active)
            if not block.get("isActive", False):
                monthly_meta["sessions"] = monthly_meta.get("sessions", 0) + 1
                monthly_meta["cost"] = monthly_meta.get("cost", 0) + block.get("costUSD", 0)
                processed_sessions.append(block["id"])
                new_sessions_found += 1
        
        if new_sessions_found > 0:
            print(f"{Colors.GREEN}Found {new_sessions_found} new completed sessions.{Colors.ENDC}")
            config["monthly_meta"] = monthly_meta
            config["processed_sessions"] = processed_sessions
    
    config["last_incremental_update"] = datetime.now().strftime('%Y-%m-%d')
    os.system('cls' if os.name == 'nt' else 'clear')

    save_config(config)
    
    # --- Loop state variables ---
    config_instance = Config.instance()
    sessions_used = config.get("monthly_meta", {}).get("sessions", 0)
    sessions_left = config_instance.TOTAL_MONTHLY_SESSIONS - sessions_used
    cost_this_month_completed = config.get("monthly_meta", {}).get("cost", 0)
    max_tokens_so_far = config.get("max_tokens", 35000)
    
    # Obliczenia dla stopki
    next_renewal = get_next_renewal_date(args.start_day)
    days_remaining = (next_renewal - date.today()).days
    if days_remaining > 0:
        avg_sessions = sessions_left / days_remaining
    else:
        avg_sessions = float(sessions_left) # Jeśli dziś jest ostatni dzień

    cached_data = {"blocks": []}; last_fetch_time = 0
    current_session_id = None; time_alert_fired = False; inactivity_alert_fired = False
    last_activity_time = None; last_token_count = -1

    # --- Main loop ---
    while True:
        try:
            now_utc = datetime.now(config_instance.UTC_TZ)
            
            if time.time() - last_fetch_time > config_instance.CCUSAGE_FETCH_INTERVAL_SECONDS:
                today_str = datetime.now().strftime('%Y%m%d')
                fetched_data = run_ccusage(today_str)
                if fetched_data and fetched_data.get("blocks"):
                    cached_data = fetched_data
                last_fetch_time = time.time()

            active_block = None
            if "blocks" in cached_data:
                for block in cached_data["blocks"]:
                    if block.get("isGap", False): continue
                    start_time = parse_utc_time(block["startTime"])
                    end_time = parse_utc_time(block["endTime"])
                    if start_time <= now_utc <= end_time:
                        active_block = block
                        break
            
            if not active_block and current_session_id:
                # Session just ended - update monthly stats from cached data
                if "blocks" in cached_data:
                    # Filter blocks for current billing period
                    period_start = parse_utc_time(sub_start_date_str + "T00:00:00")
                    period_blocks = [b for b in cached_data["blocks"] 
                                   if not b.get("isGap", False) and 
                                   parse_utc_time(b["startTime"]) >= period_start]
                    completed_blocks = [b for b in period_blocks if not b.get("isActive", False)]
                    
                    sessions_used = len(completed_blocks)
                    cost_this_month_completed = sum(b.get("costUSD", 0) for b in completed_blocks)
                    
                    # Update config and recalculate derived values
                    config["monthly_meta"]["sessions"] = sessions_used
                    config["monthly_meta"]["cost"] = cost_this_month_completed
                    save_config(config)
                    
                    sessions_left = config_instance.TOTAL_MONTHLY_SESSIONS - sessions_used
                    if days_remaining > 0:
                        avg_sessions = sessions_left / days_remaining
                    else:
                        avg_sessions = float(sessions_left)
                
                current_session_id = None; time_alert_fired = False; inactivity_alert_fired = False
                last_activity_time = None; last_token_count = -1

            clear_screen_for_refresh()
            now_local = datetime.now(config_instance.LOCAL_TZ)
            print(f"{Colors.HEADER}{Colors.BOLD}✦ ✧ ✦ CLAUDE SESSION MONITOR ✦ ✧ ✦{Colors.ENDC}")
            print(f"{Colors.HEADER}{'=' * 35}{Colors.ENDC}\n")

            if active_block:
                if active_block['id'] != current_session_id:
                    current_session_id = active_block['id']; time_alert_fired = False
                    inactivity_alert_fired = False; last_activity_time = now_utc
                    last_token_count = active_block.get("totalTokens", 0)

                tokens_current = active_block.get("totalTokens", 0)
                if tokens_current > max_tokens_so_far:
                    max_tokens_so_far = tokens_current
                    config["max_tokens"] = max_tokens_so_far
                    save_config(config)

                token_limit = max_tokens_so_far
                token_usage_percent = (tokens_current / token_limit) * 100 if token_limit > 0 else 0
                
                end_time = parse_utc_time(active_block["endTime"])
                time_remaining = end_time - now_utc
                time_total = end_time - parse_utc_time(active_block["startTime"])
                time_progress_percent = (1 - (time_remaining.total_seconds() / time_total.total_seconds())) * 100

                if not time_alert_fired and time_remaining < timedelta(minutes=config_instance.TIME_REMAINING_ALERT_MINUTES):
                    show_macos_notification("Claude Monitor", f"Less than {config_instance.TIME_REMAINING_ALERT_MINUTES} minutes remaining in the session.")
                    time_alert_fired = True

                if tokens_current > last_token_count:
                    last_activity_time = now_utc; last_token_count = tokens_current; inactivity_alert_fired = False
                else:
                    inactive_duration = now_utc - last_activity_time
                    if not inactivity_alert_fired and inactive_duration > timedelta(minutes=config_instance.INACTIVITY_ALERT_MINUTES):
                        show_macos_notification("Claude Monitor", f"No activity for {config_instance.INACTIVITY_ALERT_MINUTES} minutes.")
                        inactivity_alert_fired = True
                
                cost_current_session = active_block.get("costUSD", 0)
                total_cost_display = cost_this_month_completed - active_block.get("costUSD", 0) + cost_current_session

                print(f"Token Usage:   {Colors.GREEN}{create_progress_bar(token_usage_percent)}{Colors.ENDC} {token_usage_percent:.1f}%")
                print(f"Time to Reset: {Colors.BLUE}{create_progress_bar(time_progress_percent)}{Colors.ENDC} {format_timedelta(time_remaining)}")
                print(f"\n{Colors.BOLD}Tokens:{Colors.ENDC}        {tokens_current:,} / ~{token_limit:,}\n{Colors.BOLD}Session Cost:{Colors.ENDC}  ${cost_current_session:.2f}\n")
            else:
                total_cost_display = cost_this_month_completed
                print(f"\n{Colors.WARNING}Waiting for a new session to start...{Colors.ENDC}\n\nSaved max tokens: {int(max_tokens_so_far):,}\nCurrent subscription period started: {sub_start_date_str}\n")

            # --- Footer ---
            print("=" * 60)
            footer_line1 = f"⏰ {now_local.strftime('%H:%M:%S')}   🗓️ Sessions: {Colors.BOLD}{sessions_used} used, {sessions_left} left{Colors.ENDC} | 💰 Cost (mo): ${total_cost_display:.2f}"
            footer_line2 = f"  └─ ⏳ {days_remaining} days left (avg. {avg_sessions:.1f} sessions/day) | Ctrl+C to exit"
            print(footer_line1)
            print(footer_line2)

            time.sleep(config_instance.REFRESH_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\033[?25h", end="")  # Show cursor
            print(f"\n\n{Colors.WARNING}Closing monitor...{Colors.ENDC}")
            sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor Claude API token and cost usage.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--start-day", type=int, default=1, help="Day of the month the billing period starts.")
    parser.add_argument("--recalculate", action="store_true", help="Forces re-scanning of history to update \nstored values (max tokens and costs).")
    parser.add_argument("--test-alert", action="store_true", help="Sends a test system notification (macOS only) and exits.")
    parser.add_argument("--timezone", type=str, default="Europe/Warsaw", help="Timezone for display (e.g., 'America/New_York', 'UTC', 'Asia/Tokyo'). Default: Europe/Warsaw")
    parser.add_argument("--version", action="version", version=f"Claude Session Monitor {Config.instance().VERSION}")
    args = parser.parse_args()
    
    if args.test_alert:
        print(f"{Colors.CYAN}Sending test alert...{Colors.ENDC}")
        show_macos_notification("Test Notification", "If you see this, alerts are working correctly.")
        print(f"{Colors.GREEN}Alert sending command executed.{Colors.ENDC}")
        sys.exit(0)
    
    if not 1 <= args.start_day <= 28:
        print(f"{Colors.FAIL}Error: Start day must be between 1 and 28.{Colors.ENDC}")
        sys.exit(1)
    
    # Validate and set timezone
    try:
        config = Config.instance()
        config.set_timezone(args.timezone)
    except Exception as e:
        print(f"{Colors.FAIL}Error: Invalid timezone '{args.timezone}'. {e}{Colors.ENDC}")
        print(f"{Colors.WARNING}Common timezones: UTC, America/New_York, Europe/London, Asia/Tokyo, Australia/Sydney{Colors.ENDC}")
        sys.exit(1)
        
    main(args)
