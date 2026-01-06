"""
Configuration Manager for Trading System

This module provides a centralized configuration system that handles:
1. Default values from config.py
2. User settings from frontend
3. Runtime configuration updates
4. Validation and consistency checks

Configuration Hierarchy (highest to lowest priority):
1. Frontend Settings (user-configured via dashboard)
2. Environment Variables (.env file)
3. Config.py Defaults
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# Import default values from config.py
from src.config import (
    CASH_PERCENTAGE, TAKE_PROFIT_PERCENT, STOP_LOSS_PERCENT,
    MAX_POSITION_PERCENTAGE, SLEEP_BETWEEN_RUNS_MINUTES,
    DATA_TIMEFRAME, DAYSBACK_4_DATA, AI_MODEL_TYPE, AI_MODEL,
    AI_TEMPERATURE, AI_MAX_TOKENS, HYPERLIQUID_LEVERAGE
)

# Import settings_manager for user settings
try:
    from src.utils.settings_manager import load_settings
    SETTINGS_MANAGER_AVAILABLE = True
except ImportError:
    SETTINGS_MANAGER_AVAILABLE = False

class ConfigurationManager:
    """Centralized configuration manager with hierarchy support"""
    
    def __init__(self):
        self._config_cache = {}
        self._user_settings = {}
        self._load_user_settings()
    
    def _load_user_settings(self):
        """Load user settings from dashboard settings file"""
        try:
            # Try to use settings_manager first if available
            if SETTINGS_MANAGER_AVAILABLE:
                self._user_settings = load_settings()
                print("✅ Loaded user settings via settings_manager")
            else:
                # Fallback to direct file loading
                settings_file = Path("src/data/user_settings.json")
                if settings_file.exists():
                    with open(settings_file, 'r') as f:
                        self._user_settings = json.load(f)
                    print(f"✅ Loaded user settings from {settings_file}")
                else:
                    print("ℹ️ No user settings file found, using defaults")
        except Exception as e:
            print(f"⚠️ Error loading user settings: {e}")
            self._user_settings = {}
    
    def _get_user_setting(self, key: str, default: Any = None) -> Any:
        """Get user setting with fallback to default"""
        return self._user_settings.get(key, default)
    
    def get_cash_percentage(self) -> float:
        """Get cash reserve percentage"""
        return self._get_user_setting('cash_percentage', CASH_PERCENTAGE)
    
    def get_take_profit_percent(self) -> float:
        """Get take profit percentage"""
        return self._get_user_setting('take_profit_percent', TAKE_PROFIT_PERCENT)
    
    def get_stop_loss_percent(self) -> float:
        """Get stop loss percentage"""
        return self._get_user_setting('stop_loss_percent', STOP_LOSS_PERCENT)
    
    def get_max_position_percentage(self) -> float:
        """Get maximum position percentage"""
        return self._get_user_setting('max_position_percentage', MAX_POSITION_PERCENTAGE)
    
    def get_pnl_check_interval(self) -> int:
        """Get PnL check interval in minutes"""
        return self._get_user_setting('pnl_check_interval', SLEEP_BETWEEN_RUNS_MINUTES)
    
    def get_cycle_time(self) -> int:
        """Get trading cycle time in minutes"""
        return self._get_user_setting('cycle_time', SLEEP_BETWEEN_RUNS_MINUTES)
    
    def get_timeframe(self) -> str:
        """Get market data timeframe"""
        return self._get_user_setting('timeframe', DATA_TIMEFRAME)
    
    def get_days_back(self) -> int:
        """Get days of historical data to fetch"""
        return self._get_user_setting('days_back', DAYSBACK_4_DATA)
    
    def get_ai_provider(self) -> str:
        """Get AI model provider"""
        return self._get_user_setting('ai_provider', AI_MODEL_TYPE)
    
    def get_ai_model(self) -> str:
        """Get AI model name"""
        return self._get_user_setting('ai_model', AI_MODEL)
    
    def get_ai_temperature(self) -> float:
        """Get AI model temperature"""
        return self._get_user_setting('ai_temperature', AI_TEMPERATURE)
    
    def get_ai_max_tokens(self) -> int:
        """Get AI model max tokens"""
        return self._get_user_setting('ai_max_tokens', AI_MAX_TOKENS)
    
    def get_leverage(self) -> int:
        """Get leverage setting"""
        return self._get_user_setting('leverage', HYPERLIQUID_LEVERAGE)
    
    def get_monitored_tokens(self) -> list:
        """Get list of monitored tokens"""
        return self._get_user_setting('monitored_tokens', [])
    
    def get_swarm_mode(self) -> bool:
        """Get swarm mode setting"""
        return self._get_user_setting('swarm_mode', False)
    
    def get_swarm_models(self) -> list:
        """Get swarm models configuration"""
        return self._get_user_setting('swarm_models', [])
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update user settings and save to file"""
        self._user_settings.update(new_settings)
        self._save_user_settings()
    
    def _save_user_settings(self):
        """Save user settings to file"""
        try:
            settings_file = Path("src/data/user_settings.json")
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_file, 'w') as f:
                json.dump(self._user_settings, f, indent=2)
            
            print(f"✅ User settings saved to {settings_file}")
        except Exception as e:
            print(f"❌ Error saving user settings: {e}")
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get complete configuration for debugging"""
        return {
            'cash_percentage': self.get_cash_percentage(),
            'take_profit_percent': self.get_take_profit_percent(),
            'stop_loss_percent': self.get_stop_loss_percent(),
            'max_position_percentage': self.get_max_position_percentage(),
            'pnl_check_interval': self.get_pnl_check_interval(),
            'cycle_time': self.get_cycle_time(),
            'timeframe': self.get_timeframe(),
            'days_back': self.get_days_back(),
            'ai_provider': self.get_ai_provider(),
            'ai_model': self.get_ai_model(),
            'ai_temperature': self.get_ai_temperature(),
            'ai_max_tokens': self.get_ai_max_tokens(),
            'leverage': self.get_leverage(),
            'monitored_tokens': self.get_monitored_tokens(),
            'swarm_mode': self.get_swarm_mode(),
            'swarm_models': self.get_swarm_models(),
            'user_settings': self._user_settings
        }
    
    def validate_config(self) -> tuple[bool, list]:
        """Validate configuration values"""
        errors = []
        
        # Validate percentages
        cash_pct = self.get_cash_percentage()
        if not 0 <= cash_pct <= 100:
            errors.append(f"Cash percentage must be 0-100%, got {cash_pct}")
        
        tp_pct = self.get_take_profit_percent()
        if not 0.1 <= tp_pct <= 100:
            errors.append(f"Take profit must be 0.1-100%, got {tp_pct}")
        
        sl_pct = self.get_stop_loss_percent()
        if not -100 <= sl_pct <= -0.1:
            errors.append(f"Stop loss must be -100 to -0.1%, got {sl_pct}")
        
        max_pos_pct = self.get_max_position_percentage()
        if not 1 <= max_pos_pct <= 100:
            errors.append(f"Max position must be 1-100%, got {max_pos_pct}")
        
        # Validate intervals
        pnl_interval = self.get_pnl_check_interval()
        if not 1 <= pnl_interval <= 60:
            errors.append(f"PnL check interval must be 1-60 minutes, got {pnl_interval}")
        
        cycle_time = self.get_cycle_time()
        if not 1 <= cycle_time <= 1440:
            errors.append(f"Cycle time must be 1-1440 minutes, got {cycle_time}")
        
        # Validate AI settings
        temp = self.get_ai_temperature()
        if not 0 <= temp <= 1:
            errors.append(f"AI temperature must be 0-1, got {temp}")
        
        max_tokens = self.get_ai_max_tokens()
        if not 100 <= max_tokens <= 100000:
            errors.append(f"AI max tokens must be 100-100000, got {max_tokens}")
        
        return len(errors) == 0, errors

# Global configuration manager instance
config_manager = ConfigurationManager()

# Convenience functions for backward compatibility
def get_cash_percentage() -> float:
    return config_manager.get_cash_percentage()

def get_take_profit_percent() -> float:
    return config_manager.get_take_profit_percent()

def get_stop_loss_percent() -> float:
    return config_manager.get_stop_loss_percent()

def get_max_position_percentage() -> float:
    return config_manager.get_max_position_percentage()

def get_pnl_check_interval() -> int:
    return config_manager.get_pnl_check_interval()

def get_cycle_time() -> int:
    return config_manager.get_cycle_time()

def get_timeframe() -> str:
    return config_manager.get_timeframe()

def get_days_back() -> int:
    return config_manager.get_days_back()

def get_ai_provider() -> str:
    return config_manager.get_ai_provider()

def get_ai_model() -> str:
    return config_manager.get_ai_model()

def get_ai_temperature() -> float:
    return config_manager.get_ai_temperature()

def get_ai_max_tokens() -> int:
    return config_manager.get_ai_max_tokens()

def get_leverage() -> int:
    return config_manager.get_leverage()

def get_monitored_tokens() -> list:
    return config_manager.get_monitored_tokens()

def get_swarm_mode() -> bool:
    return config_manager.get_swarm_mode()

def get_swarm_models() -> list:
    return config_manager.get_swarm_models()

def update_settings(new_settings: Dict[str, Any]):
    """Update settings from frontend"""
    config_manager.update_settings(new_settings)

def validate_config() -> tuple[bool, list]:
    """Validate current configuration"""
    return config_manager.validate_config()

def get_all_config() -> Dict[str, Any]:
    """Get complete configuration"""
    return config_manager.get_all_config()
