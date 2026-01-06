#!/usr/bin/env python3
"""
Simple test to verify basic configuration updates
"""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

def test_basic_imports():
    """Test basic imports work"""
    print("🧪 Testing Basic Imports...")
    
    try:
        # Test TP/SL utility
        from src.utils.take_profit_stop_loss import TP_THRESHOLD, SL_THRESHOLD, CASH_RESERVE_PCT
        print(f"✅ TP/SL Utility: TP={TP_THRESHOLD}%, SL={SL_THRESHOLD}%, Cash={CASH_RESERVE_PCT}%")
        
        # Test trading agent config
        from src.agents.trading_agent import PNL_CHECK_INTERVAL, MAX_POSITION_PERCENTAGE
        print(f"✅ Trading Agent: PnL Check={PNL_CHECK_INTERVAL}min, Max Position={MAX_POSITION_PERCENTAGE}%")
        
        # Test config module
        from src.config import CASH_PERCENTAGE, TAKE_PROFIT_PERCENT, STOP_LOSS_PERCENT
        print(f"✅ Config Module: Cash={CASH_PERCENTAGE}%, TP={TAKE_PROFIT_PERCENT}%, SL={STOP_LOSS_PERCENT}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_frontend_files():
    """Test frontend files exist and have expected content"""
    print("\n🧪 Testing Frontend Files...")
    
    try:
        # Check HTML has new fields
        html_path = Path("dashboard/templates/index.html")
        html_content = html_path.read_text()
        
        if 'pnl-check-interval-input' in html_content:
            print("✅ PnL Check Interval field found in HTML")
        else:
            print("❌ PnL Check Interval field missing")
            return False
            
        if 'max-position-input' in html_content:
            print("✅ Max Position field found in HTML")
        else:
            print("❌ Max Position field missing")
            return False
            
        if 'cash-reserve-input' in html_content:
            print("✅ Cash Reserve field found in HTML")
        else:
            print("❌ Cash Reserve field missing")
            return False
        
        # Check JavaScript has validation
        js_path = Path("dashboard/static/app.js")
        js_content = js_path.read_text()
        
        if 'pnlCheckInterval' in js_content and 'maxPosition' in js_content:
            print("✅ JavaScript validation includes new fields")
        else:
            print("❌ JavaScript validation missing new fields")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Frontend test error: {e}")
        return False

def main():
    """Run simple tests"""
    print("🚀 Running Simple Configuration Tests...\n")
    
    tests = [
        test_basic_imports,
        test_frontend_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
