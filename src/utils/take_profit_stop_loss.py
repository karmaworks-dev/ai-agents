"""
Take Profit and Stop Loss Utility Module
=======================================

Standalone utility that monitors positions every 30 seconds and automatically
closes positions when TP/SL thresholds are hit, while enforcing cash reserve requirements.

Configuration:
- Uses TAKE_PROFIT_THRESHOLD and STOP_LOSS_THRESHOLD from config.py
- Enforces CASH_PERCENTAGE reserve for fee payments
- Runs independently of main trading cycle

Integration:
- Import in trading_agent.py and start as daemon thread
- Uses existing position checking and closing functions
"""

import time
import threading
from datetime import datetime
from termcolor import cprint

# Import configuration values
from src.config import CASH_PERCENTAGE
from src.utils.close_validator import TAKE_PROFIT_THRESHOLD, STOP_LOSS_THRESHOLD

# Import necessary functions from HyperLiquid utilities
from src.nice_funcs_hyperliquid import (
    get_position, 
    close_complete_position, 
    get_account_value, 
    get_available_balance
)

# Use exact values from config.py
TP_THRESHOLD = TAKE_PROFIT_THRESHOLD  # 6.0%
SL_THRESHOLD = STOP_LOSS_THRESHOLD    # -2.0%
CASH_RESERVE_PCT = CASH_PERCENTAGE    # 10%

def enforce_cash_reserve(account) -> bool:
    """
    Ensure CASH_PERCENTAGE is maintained before closing positions.
    
    Returns:
        bool: True if closing position maintains cash reserve, False otherwise
    """
    try:
        total_value = get_account_value(account.address if hasattr(account, 'address') else account)
        required_reserve = total_value * (CASH_RESERVE_PCT / 100)
        current_balance = get_available_balance(account.address if hasattr(account, 'address') else account)
        
        # If we have enough buffer, allow closing
        can_close = current_balance >= required_reserve
        if not can_close:
            cprint(f"⚠️  Cash reserve insufficient: ${current_balance:.2f} < ${required_reserve:.2f} required", "yellow")
        
        return can_close
    except Exception as e:
        cprint(f"❌ Error enforcing cash reserve: {e}", "red")
        # On error, be conservative and don't close
        return False

def check_tp_sl_positions(account) -> list:
    """
    Check all positions for TP/SL triggers and close if needed.
    
    Args:
        account: HyperLiquid account object
        
    Returns:
        list: List of symbols that were closed
    """
    closed_positions = []
    
    try:
        # Import symbols from config
        from src.config import get_active_tokens
        symbols = get_active_tokens()
        
        cprint(f"🔍 TP/SL Check: Monitoring {len(symbols)} positions...", "cyan")
        
        for symbol in symbols:
            try:
                # Skip excluded tokens
                from src.config import EXCLUDED_TOKENS
                if symbol in EXCLUDED_TOKENS:
                    continue
                
                # Get position data
                pos_data = get_position(symbol, account)
                _, im_in_pos, _, _, _, pnl_perc, _ = pos_data
                
                if not im_in_pos:
                    continue
                
                # Check TP threshold (6.0%)
                if pnl_perc >= TP_THRESHOLD:
                    cprint(f"🎯 TAKE PROFIT: {symbol} at +{pnl_perc:.2f}% (threshold: +{TP_THRESHOLD}%)", "green")
                    if enforce_cash_reserve(account):
                        cprint(f"🔒 Closing {symbol} - Cash reserve maintained", "green")
                        close_result = close_complete_position(symbol, account)
                        if close_result:
                            closed_positions.append(symbol)
                            cprint(f"✅ Closed {symbol} for profit", "green", attrs=["bold"])
                        else:
                            cprint(f"❌ Failed to close {symbol}", "red")
                    else:
                        cprint(f"⚠️  Skipping {symbol} close - Cash reserve would be violated", "yellow")
                
                # Check SL threshold (-2.0%)
                elif pnl_perc <= SL_THRESHOLD:
                    cprint(f"🚨 STOP LOSS: {symbol} at {pnl_perc:.2f}% (threshold: {SL_THRESHOLD}%)", "red")
                    if enforce_cash_reserve(account):
                        cprint(f"🔒 Closing {symbol} - Cash reserve maintained", "green")
                        close_result = close_complete_position(symbol, account)
                        if close_result:
                            closed_positions.append(symbol)
                            cprint(f"✅ Closed {symbol} for loss", "green", attrs=["bold"])
                        else:
                            cprint(f"❌ Failed to close {symbol}", "red")
                    else:
                        cprint(f"⚠️  Skipping {symbol} close - Cash reserve would be violated", "yellow")
                        
            except Exception as e:
                cprint(f"⚠️  Error checking {symbol}: {e}", "yellow")
                continue
                
        if closed_positions:
            cprint(f"📊 TP/SL Check Complete: Closed {len(closed_positions)} positions", "cyan")
        else:
            cprint("📊 TP/SL Check Complete: No positions closed", "cyan")
            
    except Exception as e:
        cprint(f"❌ Error in TP/SL check: {e}", "red")
        
    return closed_positions

def run_tp_sl_monitor(account, interval=30):
    """
    Main monitoring loop that runs every 30 seconds.
    
    Args:
        account: HyperLiquid account object
        interval: Check interval in seconds (default: 30)
    """
    cprint(f"🚀 TP/SL Monitor Started: Checking every {interval} seconds", "green", attrs=["bold"])
    cprint(f"📈 TP Threshold: +{TP_THRESHOLD}%", "cyan")
    cprint(f"📉 SL Threshold: {SL_THRESHOLD}%", "cyan")
    cprint(f"💰 Cash Reserve: {CASH_RESERVE_PCT}%", "cyan")
    
    while True:
        try:
            # Run TP/SL check
            check_tp_sl_positions(account)
            
            # Wait for next check
            time.sleep(interval)
            
        except KeyboardInterrupt:
            cprint("\n👋 TP/SL Monitor shutting down...", "blue")
            break
        except Exception as e:
            cprint(f"❌ Error in TP/SL monitor: {e}", "red")
            time.sleep(interval)  # Continue monitoring despite errors

# Example usage (for testing):
# if __name__ == "__main__":
#     from src.nice_funcs_hyperliquid import _get_account_from_env
#     account = _get_account_from_env()
#     run_tp_sl_monitor(account)
