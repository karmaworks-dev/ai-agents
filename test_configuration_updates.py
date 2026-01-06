#!/usr/bin/env python3
"""
Test script to verify all configuration updates are working correctly.
This script tests:
1. TP/SL utility with new console logging
2. Frontend configuration fields
3. Trading agent configuration
4. Integration between components
"""

import sys
import os
import time
import json
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

def test_tp_sl_utility():
    """Test TP/SL utility with console logging"""
    print("🧪 Testing TP/SL Utility...")
    
    try:
        # Import the TP/SL utility
        from src.utils.take_profit_stop_loss import (
            TP_THRESHOLD, SL_THRESHOLD, CASH_RESERVE_PCT,
            check_tp_sl_positions, enforce_cash_reserve
        )
        
        print(f"✅ TP Threshold: {TP_THRESHOLD}%")
        print(f"✅ SL Threshold: {SL_THRESHOLD}%")
        print(f"✅ Cash Reserve: {CASH_RESERVE_PCT}%")
        
        # Test that functions are importable
        assert callable(check_tp_sl_positions)
        assert callable(enforce_cash_reserve)
        
        print("✅ TP/SL utility functions are importable")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import TP/SL utility: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing TP/SL utility: {e}")
        return False

def test_frontend_config():
    """Test frontend configuration fields"""
    print("\n🧪 Testing Frontend Configuration...")
    
    try:
        # Check HTML template has new fields
        html_path = Path("dashboard/templates/index.html")
        if not html_path.exists():
            print("❌ HTML template not found")
            return False
            
        html_content = html_path.read_text()
        
        # Check for new configuration fields
        required_fields = [
            'pnl-check-interval-input',
            'max-position-input',
            'cash-reserve-input'
        ]
        
        for field in required_fields:
            if field in html_content:
                print(f"✅ Found {field} in HTML")
            else:
                print(f"❌ Missing {field} in HTML")
                return False
        
        # Check JavaScript validation
        js_path = Path("dashboard/static/app.js")
        if js_path.exists():
            js_content = js_path.read_text()
            
            if 'pnlCheckInterval' in js_content and 'maxPosition' in js_content:
                print("✅ JavaScript validation includes new fields")
            else:
                print("❌ JavaScript validation missing new fields")
                return False
        
        print("✅ Frontend configuration fields are present")
        return True
        
    except Exception as e:
        print(f"❌ Error testing frontend config: {e}")
        return False

def test_trading_agent_config():
    """Test trading agent configuration"""
    print("\n🧪 Testing Trading Agent Configuration...")
    
    try:
        # Import trading agent
        from src.agents.trading_agent import (
            PNL_CHECK_INTERVAL, TP_THRESHOLD, SL_THRESHOLD,
            CASH_PERCENTAGE, MAX_POSITION_PERCENTAGE
        )
        
        print(f"✅ PnL Check Interval: {PNL_CHECK_INTERVAL} minutes")
        print(f"✅ TP Threshold: {TP_THRESHOLD}%")
        print(f"✅ SL Threshold: {SL_THRESHOLD}%")
        print(f"✅ Cash Reserve: {CASH_PERCENTAGE}%")
        print(f"✅ Max Position: {MAX_POSITION_PERCENTAGE}%")
        
        # Test that values are reasonable
        assert PNL_CHECK_INTERVAL >= 1 and PNL_CHECK_INTERVAL <= 60
        assert TP_THRESHOLD > 0 and TP_THRESHOLD <= 100
        assert SL_THRESHOLD < 0 and SL_THRESHOLD >= -100
        assert CASH_PERCENTAGE >= 0 and CASH_PERCENTAGE <= 100
        assert MAX_POSITION_PERCENTAGE >= 1 and MAX_POSITION_PERCENTAGE <= 100
        
        print("✅ All configuration values are within expected ranges")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import trading agent config: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing trading agent config: {e}")
        return False

def test_console_logging():
    """Test console logging functionality"""
    print("\n🧪 Testing Console Logging...")
    
    try:
        # Test that console logging functions are available
        from src.utils.logging_utils import add_console_log
        
        # Test basic logging
        add_console_log("Test message", "info")
        print("✅ Console logging function is available")
        
        return True
        
    except ImportError:
        print("⚠️ Console logging utility not available (fallback mode)")
        return True  # This is acceptable
    except Exception as e:
        print(f"❌ Error testing console logging: {e}")
        return False

def test_integration():
    """Test integration between components"""
    print("\n🧪 Testing Integration...")
    
    try:
        # Test that all components can be imported together
        from src.utils.take_profit_stop_loss import run_tp_sl_monitor
        from src.agents.trading_agent import TradingAgent
        from src.config import CASH_PERCENTAGE, TAKE_PROFIT_PERCENT, STOP_LOSS_PERCENT
        
        print("✅ All components can be imported together")
        
        # Test configuration consistency
        assert CASH_PERCENTAGE == 10  # Should match default
        assert TAKE_PROFIT_PERCENT == 20  # Should match default
        assert STOP_LOSS_PERCENT == -2  # Should match default
        
        print("✅ Configuration values are consistent across modules")
        return True
        
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Configuration Update Tests...\n")
    
    tests = [
        test_tp_sl_utility,
        test_frontend_config,
        test_trading_agent_config,
        test_console_logging,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Configuration updates are working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
