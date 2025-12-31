"""
Position Tracker for AI Trading System
=======================================
Tracks position entry times for age-based decision making.

Features:
- Records position entry timestamps
- Calculates position age in hours
- Handles bot restarts gracefully
- Thread-safe operations
"""

import json
import os
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

# Position tracker file location
TRACKER_FILE = Path(__file__).parent.parent / "data" / "position_tracker.json"

# Thread lock for file operations
_tracker_lock = threading.Lock()


def _load_tracker() -> Dict:
    """Load position tracker from file"""
    try:
        if TRACKER_FILE.exists():
            with open(TRACKER_FILE, 'r') as f:
                return json.load(f)
        return {"positions": {}, "last_updated": None}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Position tracker corrupted, creating fresh tracker: {e}")
        return {"positions": {}, "last_updated": None}


def _save_tracker(data: Dict) -> bool:
    """Save position tracker to file"""
    try:
        # Ensure directory exists
        TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)

        data["last_updated"] = datetime.now(timezone.utc).isoformat()

        with open(TRACKER_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving position tracker: {e}")
        return False


def record_position_entry(symbol: str, entry_price: float, size: float,
                          is_long: bool) -> bool:
    """
    Record a new position entry with timestamp.

    Args:
        symbol: Token symbol (e.g., 'BTC', 'ETH')
        entry_price: Entry price
        size: Position size
        is_long: True for long, False for short

    Returns:
        True if recorded successfully
    """
    with _tracker_lock:
        tracker = _load_tracker()

        tracker["positions"][symbol] = {
            "entry_time": datetime.now(timezone.utc).isoformat(),
            "entry_price": entry_price,
            "size": size,
            "is_long": is_long,
            "direction": "LONG" if is_long else "SHORT"
        }

        return _save_tracker(tracker)


def remove_position(symbol: str) -> bool:
    """
    Remove a position from tracker when closed.

    Args:
        symbol: Token symbol to remove

    Returns:
        True if removed successfully
    """
    with _tracker_lock:
        tracker = _load_tracker()

        if symbol in tracker["positions"]:
            del tracker["positions"][symbol]
            return _save_tracker(tracker)

        return True  # Position wasn't tracked, that's OK


def get_position_age_hours(symbol: str) -> float:
    """
    Get the age of a position in hours.

    Args:
        symbol: Token symbol

    Returns:
        Age in hours, or 0.0 if position not tracked (assumes new)
    """
    with _tracker_lock:
        tracker = _load_tracker()

        if symbol not in tracker["positions"]:
            return 0.0  # Not tracked = treat as brand new (safety first)

        try:
            entry_time_str = tracker["positions"][symbol]["entry_time"]
            entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))

            # Ensure entry_time is timezone-aware
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            age_seconds = (now - entry_time).total_seconds()
            age_hours = age_seconds / 3600

            return max(0.0, age_hours)  # Never return negative

        except Exception as e:
            print(f"Warning: Error calculating age for {symbol}: {e}")
            return 0.0  # Default to new if error


def get_position_info(symbol: str) -> Optional[Dict]:
    """
    Get full position info from tracker.

    Args:
        symbol: Token symbol

    Returns:
        Position dict or None if not tracked
    """
    with _tracker_lock:
        tracker = _load_tracker()
        return tracker["positions"].get(symbol)


def get_all_tracked_positions() -> Dict:
    """
    Get all tracked positions.

    Returns:
        Dict of symbol -> position info
    """
    with _tracker_lock:
        tracker = _load_tracker()
        return tracker["positions"].copy()


def sync_with_exchange_positions(exchange_positions: Dict) -> Tuple[int, int]:
    """
    Sync tracker with actual exchange positions.

    - Adds positions from exchange that aren't tracked
    - Removes tracked positions that no longer exist on exchange

    Args:
        exchange_positions: Dict of symbol -> position data from exchange

    Returns:
        Tuple of (positions_added, positions_removed)
    """
    with _tracker_lock:
        tracker = _load_tracker()
        added = 0
        removed = 0

        # Add new positions from exchange
        for symbol, pos_data in exchange_positions.items():
            if symbol not in tracker["positions"]:
                # New position not in tracker - add with current time
                # (Assumes age = 0 for safety)
                is_long = pos_data.get("is_long", True)
                tracker["positions"][symbol] = {
                    "entry_time": datetime.now(timezone.utc).isoformat(),
                    "entry_price": pos_data.get("entry_price", 0),
                    "size": pos_data.get("size", 0),
                    "is_long": is_long,
                    "direction": "LONG" if is_long else "SHORT",
                    "note": "Added during sync - actual age unknown"
                }
                added += 1

        # Remove positions no longer on exchange
        tracked_symbols = list(tracker["positions"].keys())
        for symbol in tracked_symbols:
            if symbol not in exchange_positions:
                del tracker["positions"][symbol]
                removed += 1

        if added > 0 or removed > 0:
            _save_tracker(tracker)

        return added, removed


def update_position_entry_price(symbol: str, new_entry_price: float) -> bool:
    """
    Update entry price for a position (e.g., after averaging).

    Args:
        symbol: Token symbol
        new_entry_price: Updated entry price

    Returns:
        True if updated successfully
    """
    with _tracker_lock:
        tracker = _load_tracker()

        if symbol in tracker["positions"]:
            tracker["positions"][symbol]["entry_price"] = new_entry_price
            return _save_tracker(tracker)

        return False


def clear_all_positions() -> bool:
    """
    Clear all tracked positions (use with caution).

    Returns:
        True if cleared successfully
    """
    with _tracker_lock:
        tracker = {"positions": {}, "last_updated": None}
        return _save_tracker(tracker)
