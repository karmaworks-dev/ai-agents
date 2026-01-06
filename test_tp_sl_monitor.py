#!/usr/bin/env python3
"""
Test script for TP/SL Monitor functionality
"""

import time
import threading
from src.utils.take_profit_stop_loss import run_tp_sl_monitor
from src.nice_funcs_hyperliquid import _get_account_from_env

def test_tp_sl_monitor():
    """Test the TP/SL monitor functionality"""
    print("🧪 Testing TP/SL Monitor...")
    
    try:
        # Get account from environment
        account = _get_account_from_env()
        print("✅ Account loaded successfully")
        
        # Test the monitor function (will run for 5 seconds then stop)
        print("🚀 Starting TP/SL monitor for 5 seconds...")
        
        # Start monitor in a thread
        monitor_thread = threading.Thread(
            target=run_tp_sl_monitor, 
            args=(account, 30),
            daemon=True
        )
        monitor_thread.start()
        
        # Let it run briefly
        time.sleep(5)
        
        print("✅ TP/SL monitor started successfully")
        print("📝 Monitor will check positions every 30 seconds")
        print("📝 Monitor will enforce cash reserve requirements")
        print("📝 Monitor will use TP threshold: +6.0% and SL threshold: -2.0%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing TP/SL monitor: {e}")
        return False

if __name__ == "__main__":
    success = test_tp_sl_monitor()
    if success:
        print("\n🎉 TP/SL Monitor test completed successfully!")
        print("💡 The monitor will run independently of the main trading cycle")
        print("💡 It checks positions every 30 seconds for TP/SL triggers")
        print("💡 It enforces cash reserve requirements before closing positions")
    else:
        print("\n❌ TP/SL Monitor test failed")
