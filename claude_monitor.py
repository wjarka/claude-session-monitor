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

# --- Configuration ---
VERSION = "1.0.0"
TOTAL_MONTHLY_SESSIONS = 50
REFRESH_INTERVAL_SECONDS = 1
CCUSAGE_FETCH_INTERVAL_SECONDS = 10
CONFIG_DIR = os.path.expanduser("~/.config/claude-monitor")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# --- Alert Configuration (macOS only) ---
TIME_REMAINING_ALERT_MINUTES = 30
INACTIVITY_ALERT_MINUTES = 10

# --- Time Zones ---
UTC_TZ = ZoneInfo("UTC")
LOCAL_TZ = ZoneInfo("Europe/Warsaw")

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
    print("\033[H\033[J", end="")

def parse_utc_time(time_str: str) -> datetime:
    time_str = time_str.split('.')[0]
    return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC_TZ)

def save_config(data: dict):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError: pass

def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE): return {}
    try:
        with open(CONFIG_FILE, 'r') as f: return json.load(f)
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
    
    # Step 1: Determine max_tokens
    max_tokens_so_far = config.get("max_tokens")
    if not max_tokens_so_far or args.recalculate:
        print(f"{Colors.WARNING}Scanning history to find maximum tokens...{Colors.ENDC}")
        full_history = run_ccusage()
        if full_history and "blocks" in full_history:
            all_tokens = [b.get("totalTokens", 0) for b in full_history["blocks"] if not b.get("isGap", False)]
            if all_tokens:
                max_tokens_so_far = max(all_tokens)
                config["max_tokens"] = max_tokens_so_far
                print(f"{Colors.GREEN}New maximum found and saved: {max_tokens_so_far:,} tokens.{Colors.ENDC}")
        time.sleep(2); os.system('cls' if os.name == 'nt' else 'clear')

    if not config.get("max_tokens"): config["max_tokens"] = 35000

    # Step 2: Determine costs and sessions for the current period
    sub_start_date = get_subscription_period_start(args.start_day)
    sub_start_date_str = sub_start_date.strftime('%Y-%m-%d')
    
    monthly_meta = config.get("monthly_meta", {})
    if args.recalculate or monthly_meta.get("period_start") != sub_start_date_str:
        print(f"{Colors.WARNING}Calculating statistics for the new period (from {sub_start_date_str})...{Colors.ENDC}")
        monthly_data = run_ccusage(sub_start_date.strftime('%Y%m%d'))
        
        sessions_used = 0; cost_this_month = 0.0
        if "blocks" in monthly_data:
            non_gap_blocks = [b for b in monthly_data["blocks"] if not b.get("isGap", False)]
            sessions_used = len(non_gap_blocks)
            cost_this_month = sum(b.get("costUSD", 0) for b in non_gap_blocks)
            
        monthly_meta = {"period_start": sub_start_date_str, "cost": cost_this_month, "sessions": sessions_used}
        config["monthly_meta"] = monthly_meta
        time.sleep(2); os.system('cls' if os.name == 'nt' else 'clear')

    save_config(config)
    
    # --- Loop state variables ---
    sessions_used = config.get("monthly_meta", {}).get("sessions", 0)
    sessions_left = TOTAL_MONTHLY_SESSIONS - sessions_used
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
            now_utc = datetime.now(UTC_TZ)
            
            if time.time() - last_fetch_time > CCUSAGE_FETCH_INTERVAL_SECONDS:
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
                # Session just ended - update monthly stats
                monthly_data = run_ccusage(sub_start_date.strftime('%Y%m%d'))
                if "blocks" in monthly_data:
                    non_gap_blocks = [b for b in monthly_data["blocks"] if not b.get("isGap", False)]
                    sessions_used = len(non_gap_blocks)
                    cost_this_month_completed = sum(b.get("costUSD", 0) for b in non_gap_blocks)
                    
                    # Update config and recalculate derived values
                    config["monthly_meta"]["sessions"] = sessions_used
                    config["monthly_meta"]["cost"] = cost_this_month_completed
                    save_config(config)
                    
                    sessions_left = TOTAL_MONTHLY_SESSIONS - sessions_used
                    if days_remaining > 0:
                        avg_sessions = sessions_left / days_remaining
                    else:
                        avg_sessions = float(sessions_left)
                
                current_session_id = None; time_alert_fired = False; inactivity_alert_fired = False
                last_activity_time = None; last_token_count = -1

            clear_screen_for_refresh()
            now_local = datetime.now(LOCAL_TZ)
            print(f"{Colors.HEADER}{Colors.BOLD}✦ ✧ ✦ CLAUDE TOKEN MONITOR ✦ ✧ ✦{Colors.ENDC}")
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

                if not time_alert_fired and time_remaining < timedelta(minutes=TIME_REMAINING_ALERT_MINUTES):
                    show_macos_notification("Claude Monitor", f"Less than {TIME_REMAINING_ALERT_MINUTES} minutes remaining in the session.")
                    time_alert_fired = True

                if tokens_current > last_token_count:
                    last_activity_time = now_utc; last_token_count = tokens_current; inactivity_alert_fired = False
                else:
                    inactive_duration = now_utc - last_activity_time
                    if not inactivity_alert_fired and inactive_duration > timedelta(minutes=INACTIVITY_ALERT_MINUTES):
                        show_macos_notification("Claude Monitor", f"No activity for {INACTIVITY_ALERT_MINUTES} minutes.")
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

            time.sleep(REFRESH_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}Closing monitor...{Colors.ENDC}")
            sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor Claude API token and cost usage.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--start-day", type=int, default=1, help="Day of the month the billing period starts.")
    parser.add_argument("--recalculate", action="store_true", help="Forces re-scanning of history to update \nstored values (max tokens and costs).")
    parser.add_argument("--test-alert", action="store_true", help="Sends a test system notification (macOS only) and exits.")
    parser.add_argument("--version", action="version", version=f"Claude Session Monitor {VERSION}")
    args = parser.parse_args()
    
    if args.test_alert:
        print(f"{Colors.CYAN}Sending test alert...{Colors.ENDC}")
        show_macos_notification("Test Notification", "If you see this, alerts are working correctly.")
        print(f"{Colors.GREEN}Alert sending command executed.{Colors.ENDC}")
        sys.exit(0)
    
    if not 1 <= args.start_day <= 28:
        print(f"{Colors.FAIL}Error: Start day must be between 1 and 28.{Colors.ENDC}")
        sys.exit(1)
        
    main(args)
