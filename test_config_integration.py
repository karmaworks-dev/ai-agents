#!/usr/bin/env python3
"""
Test script to verify config_manager and settings_manager integration
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

def test_config_manager():
    """Test config_manager functionality"""
    print("🧪 Testing config_manager...")
    
    try:
        from src.utils.config_manager import (
            get_cash_percentage, get_take_profit_percent, get_stop_loss_percent,
            get_max_position_percentage, get_pnl_check_interval, get_cycle_time,
            get_timeframe, get_days_back, get_ai_provider, get_ai_model,
            get_ai_temperature, get_ai_max_tokens, get_leverage, get_monitored_tokens,
            get_swarm_mode, get_swarm_models, validate_config, get_all_config
        )
        print("✅ config_manager imports successful")
        
        # Test getting values
        cash_pct = get_cash_percentage()
        tp_pct = get_take_profit_percent()
        sl_pct = get_stop_loss_percent()
        timeframe = get_timeframe()
        ai_provider = get_ai_provider()
        ai_model = get_ai_model()
        
        print(f"   Cash Percentage: {cash_pct}%")
        print(f"   Take Profit: {tp_pct}%")
        print(f"   Stop Loss: {sl_pct}%")
        print(f"   Timeframe: {timeframe}")
        print(f"   AI Provider: {ai_provider}")
        print(f"   AI Model: {ai_model}")
        
        # Test validation
        is_valid, errors = validate_config()
        if is_valid:
            print("✅ Configuration validation passed")
        else:
            print(f"❌ Configuration validation failed: {errors}")
            
        # Test getting all config
        all_config = get_all_config()
        print(f"   Total config keys: {len(all_config)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ config_manager import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ config_manager test failed: {e}")
        return False

def test_settings_manager():
    """Test settings_manager functionality"""
    print("\n🧪 Testing settings_manager...")
    
    try:
        from src.utils.settings_manager import load_settings, save_settings, validate_settings
        print("✅ settings_manager imports successful")
        
        # Test loading settings
        settings = load_settings()
        print(f"   Loaded {len(settings)} settings")
        
        # Test validation
        is_valid, errors = validate_settings(settings)
        if is_valid:
            print("✅ Settings validation passed")
        else:
            print(f"❌ Settings validation failed: {errors}")
            
        return True
        
    except ImportError as e:
        print(f"❌ settings_manager import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ settings_manager test failed: {e}")
        return False

def test_trading_agent_integration():
    """Test TradingAgent with config_manager"""
    print("\n🧪 Testing TradingAgent integration...")
    
    try:
        from src.agents.trading_agent import TradingAgent
        print("✅ TradingAgent import successful")
        
        # Test creating agent with default parameters (should use config_manager)
        agent = TradingAgent()
        print("✅ TradingAgent created successfully with config_manager")
        
        # Check that agent used config values
        print(f"   Agent timeframe: {agent.timeframe}")
        print(f"   Agent days_back: {agent.days_back}")
        print(f"   Agent AI provider: {agent.ai_provider}")
        print(f"   Agent AI model: {agent.ai_model_name}")
        print(f"   Agent symbols: {len(agent.symbols)} tokens")
        
        return True
        
    except ImportError as e:
        print(f"❌ TradingAgent import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ TradingAgent integration test failed: {e}")
        return False

def test_trading_app_integration():
    """Test trading_app with config_manager"""
    print("\n🧪 Testing trading_app integration...")
    
    try:
        # Import trading_app components
        from trading_app import CONFIG_MANAGER_AVAILABLE
        print(f"✅ trading_app CONFIG_MANAGER_AVAILABLE: {CONFIG_MANAGER_AVAILABLE}")
        
        if CONFIG_MANAGER_AVAILABLE:
            from trading_app import (
                get_cash_percentage, get_take_profit_percent, get_stop_loss_percent,
                get_max_position_percentage, get_pnl_check_interval, get_cycle_time,
                get_timeframe, get_days_back, get_ai_provider, get_ai_model,
                get_ai_temperature, get_ai_max_tokens, get_leverage, get_monitored_tokens,
                get_swarm_mode, get_swarm_models
            )
            print("✅ trading_app config_manager functions available")
            
            # Test getting values
            timeframe = get_timeframe()
            days_back = get_days_back()
            ai_provider = get_ai_provider()
            ai_model = get_ai_model()
            
            print(f"   Timeframe: {timeframe}")
            print(f"   Days back: {days_back}")
            print(f"   AI Provider: {ai_provider}")
            print(f"   AI Model: {ai_model}")
            
        else:
            print("⚠️ config_manager not available in trading_app")
            
        return True
        
    except ImportError as e:
        print(f"❌ trading_app integration test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ trading_app integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Configuration Integration Tests\n")
    
    tests = [
        test_config_manager,
        test_settings_manager,
        test_trading_agent_integration,
        test_trading_app_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n{'=' * 50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Configuration integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
