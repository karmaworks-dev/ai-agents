"""
Shared logging utilities for trading dashboard and agents
Prevents circular imports between trading_app.py and trading_agent.py
"""
import json
import queue
from pathlib import Path
from datetime import datetime

# Global log queue for async logging (main dashboard)
log_queue = queue.Queue(maxsize=1000)

# Separate log queue for backtest console (RBI backtesting page)
backtest_log_queue = queue.Queue(maxsize=1000)

def add_console_log(message, level="info", console_file=None):
    """
    Add a log message to console with level support

    Args:
        message (str): Log message text
        level (str): Log level - "info", "success", "error", "warning", "trade"
        console_file (Path): Optional path to console log file
    """
    try:
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "message": str(message),
            "level": level
        }

        # Add to queue if available
        try:
            log_queue.put_nowait(log_entry)
        except queue.Full:
            pass  # Queue full, skip this log

        # If console_file is provided, write directly (synchronous fallback)
        if console_file and isinstance(console_file, Path):
            try:
                # Load existing logs
                if console_file.exists():
                    try:
                        with open(console_file, 'r') as f:
                            logs = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        logs = []
                else:
                    logs = []

                # Add new entry
                logs.append(log_entry)
                logs = logs[-50:]  # Keep last 50 logs

                # Write back
                with open(console_file, 'w') as f:
                    json.dump(logs, f, indent=2)
            except Exception as e:
                print(f"⚠️ Error writing to console file: {e}")

        # Always print to console immediately
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    except Exception as e:
        print(f"⚠️ Error in add_console_log: {e}")


def log_position_open(symbol, side, size_usd, console_file=None):
    """
    Log when a trading position is opened

    Args:
        symbol (str): Trading symbol (e.g., 'BTC', 'ETH')
        side (str): Position side ('LONG' or 'SHORT')
        size_usd (float): Position size in USD
        console_file (Path): Optional path to console log file
    """
    try:
        emoji = "📈" if side == "LONG" else "📉"
        message = f"{emoji} Opened {side} {symbol} ${size_usd:.2f}"
        add_console_log(message, "trade", console_file)
    except Exception as e:
        print(f"⚠️ Error logging position open: {e}")


def add_backtest_log(message, level="info"):
    """
    Add a log message specifically for the backtest console.
    These logs appear on the backtesting dashboard, not the main trading dashboard.

    Args:
        message (str): Log message text
        level (str): Log level - "info", "success", "error", "warning"
    """
    try:
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "message": str(message),
            "level": level
        }

        # Add to backtest queue
        try:
            backtest_log_queue.put_nowait(log_entry)
        except queue.Full:
            pass  # Queue full, skip this log

        # Always print to console
        print(f"[BACKTEST {datetime.now().strftime('%H:%M:%S')}] {message}")

    except Exception as e:
        print(f"⚠️ Error in add_backtest_log: {e}")


def add_rbi_log(message, level="info", strategy_name=None):
    """
    Add an RBI/backtest log with smart routing:
    - Detailed logs go only to the backtest console
    - Start/complete notifications go to both consoles

    Args:
        message (str): Log message text
        level (str): Log level - "info", "success", "error", "warning"
        strategy_name (str): Optional strategy name for context
    """
    try:
        # Check if this is a start or complete message (goes to both consoles)
        is_summary_message = False
        if strategy_name:
            if "started" in message.lower() or "starting" in message.lower():
                is_summary_message = True
                summary_msg = f"Backtest {strategy_name} started"
            elif "completed" in message.lower() or "complete" in message.lower():
                is_summary_message = True
                summary_msg = f"Backtest {strategy_name} complete"

        # Always add to backtest console
        add_backtest_log(message, level)

        # Only add summary messages to main console
        if is_summary_message:
            add_console_log(summary_msg, level)

    except Exception as e:
        print(f"⚠️ Error in add_rbi_log: {e}")
