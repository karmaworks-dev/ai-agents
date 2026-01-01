"""
🕉️ Karma's Fast Compounding Strategy (AGR) - Corrected Version
==============================================================

Adaptive Position Sizing Module for Dynamic Risk Management

This module provides intelligent position sizing that adapts to equity curve
performance. It works alongside signal generation strategies to optimize
trade sizing based on recent performance, drawdown, and market conditions.

Key Features:
- Adaptive equity tracking with efficiency ratio
- Confidence multiplier: 0.5x to 1.5x based on performance
- Circuit breaker on consecutive losses or severe drawdown
- Daily profit targeting with progress tracking
- Hyper-phase detection for growth stages
- Combined multipliers capped at 1.5x max

Risk Parameters:
- Daily target: 0.75% (realistic compounding)
- Maximum combined multiplier: 1.5x
- Circuit breaker: 5 consecutive losses or 20% drawdown
- Warm-up period: 15 trades (matches efficiency ratio requirement)

To keep this module private, rename with prefix:
- private_karma_compounding_agr_v3.py
- secret_karma_compounding_agr_v3.py
- dev_karma_compounding_agr_v3.py

Author: Karma Trading System
Strategy Type: Adaptive Position Sizing Module
Risk Level: Medium-High (Tuned)
"""

import os
import sys
import math
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Try to import from src
try:
    from src.config import (
        LEVERAGE as DEFAULT_LEVERAGE,
        MAX_POSITION_PERCENTAGE,
        STOP_LOSS_PERCENTAGE,
        SYMBOLS,
        MONITORED_TOKENS,
        EXCHANGE
    )
except ImportError:
    # Fallback defaults
    DEFAULT_LEVERAGE = 20
    MAX_POSITION_PERCENTAGE = 90
    STOP_LOSS_PERCENTAGE = 2.0
    SYMBOLS = ['BTC', 'ETH', 'SOL']
    MONITORED_TOKENS = []
    EXCHANGE = "HYPERLIQUID"


class AdaptiveEquityTracker:
    """
    Advanced Equity Tracker with Adaptive Position Sizing
    
    Tracks equity curve and calculates confidence multipliers based on
    recent performance trends and efficiency ratios.
    """
    
    def __init__(self, lookback_trades=21, warmup_trades=15, data_dir=None):
        """
        Initialize adaptive equity tracker
        
        Args:
            lookback_trades: Number of trades to track (21 recommended)
            warmup_trades: Must be >= efficiency_ratio_length + 1 = 15
            data_dir: Directory to store data
        """
        self.lookback_trades = lookback_trades
        self.warmup_trades = max(15, warmup_trades)
        
        # Data storage
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = PROJECT_ROOT / "data" / "equity_tracker"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.equity_file = self.data_dir / "adaptive_equity_history.json"
        
        # Core tracking
        self.equity_curve = []
        self.equity_peak = 0.0
        self.total_trades = 0
        self.initial_equity = None
        
        # Adaptive parameters
        self.efficiency_ratio_length = 14
        self.adaptive_sma_min = 8
        self.adaptive_sma_max = 30
        
        # Safety tracking
        self.consecutive_losses = 0
        self.max_consecutive_losses = 5
        
        # Load existing data
        self._load_history()
        
        print(f"🕉️ Adaptive Equity Tracker initialized")
        print(f"   Lookback: {lookback_trades} trades")
        print(f"   Warm-up: {self.warmup_trades} trades")
        print(f"   Adaptive SMA range: {self.adaptive_sma_min}-{self.adaptive_sma_max}")
    
    def _load_history(self):
        """Load equity history from disk"""
        if self.equity_file.exists():
            try:
                with open(self.equity_file, 'r') as f:
                    data = json.load(f)
                    
                self.equity_curve = data.get('equity_curve', [])
                self.equity_peak = data.get('equity_peak', 0.0)
                self.total_trades = data.get('total_trades', 0)
                self.initial_equity = data.get('initial_equity', None)
                self.consecutive_losses = data.get('consecutive_losses', 0)
                
                if len(self.equity_curve) > self.lookback_trades:
                    self.equity_curve = self.equity_curve[-self.lookback_trades:]
                
                print(f"   Loaded {len(self.equity_curve)} trade history")
                
            except Exception as e:
                print(f"⚠️ Error loading equity history: {e}")
                self._reset_state()
    
    def _reset_state(self):
        """Reset to clean state"""
        self.equity_curve = []
        self.equity_peak = 0.0
        self.total_trades = 0
        self.initial_equity = None
        self.consecutive_losses = 0
    
    def _save_history(self):
        """Save equity history to disk"""
        try:
            data = {
                'equity_curve': self.equity_curve,
                'equity_peak': self.equity_peak,
                'total_trades': self.total_trades,
                'initial_equity': self.initial_equity,
                'consecutive_losses': self.consecutive_losses,
                'last_update': datetime.now().isoformat()
            }
            
            with open(self.equity_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error saving equity history: {e}")
    
    def set_initial_equity(self, equity):
        """Set initial equity (call on first trade)"""
        if self.initial_equity is None:
            self.initial_equity = float(equity)
            self.equity_peak = float(equity)
            self._save_history()
            print(f"📊 Initial equity set: ${equity:.2f}")
    
    def record_trade_close(self, closed_equity, profit_usd=0.0):
        """
        Record equity after a trade closes
        
        Args:
            closed_equity: Equity after trade closed
            profit_usd: Profit/loss from the trade
        """
        if self.initial_equity is None:
            self.set_initial_equity(closed_equity)
        
        self.equity_curve.append(float(closed_equity))
        self.total_trades += 1
        
        # Track consecutive losses
        if profit_usd < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Maintain rolling window
        if len(self.equity_curve) > self.lookback_trades:
            self.equity_curve.pop(0)
        
        # Update peak
        self.equity_peak = max(self.equity_peak, closed_equity)
        
        self._save_history()
    
    def is_in_warmup(self):
        """Check if still in warm-up period"""
        return self.total_trades < self.warmup_trades
    
    def should_stop_trading(self):
        """Circuit breaker: Stop on consecutive losses or severe drawdown"""
        if self.consecutive_losses >= self.max_consecutive_losses:
            print(f"🛑 Circuit Breaker: {self.consecutive_losses} consecutive losses")
            return True
        
        current = self.get_current_equity()
        if self.initial_equity and current > 0:
            total_drawdown = (current / self.initial_equity) - 1
            if total_drawdown < -0.20:
                print(f"🛑 Circuit Breaker: {total_drawdown*100:.1f}% drawdown from start")
                return True
        
        return False
    
    def get_average_equity(self):
        """Calculate simple average of equity curve"""
        if not self.equity_curve:
            return 0.0
        return sum(self.equity_curve) / len(self.equity_curve)
    
    def get_current_equity(self):
        """Get most recent equity value"""
        if not self.equity_curve:
            return 0.0
        return self.equity_curve[-1]
    
    def calculate_drawdown(self, current_equity=None):
        """Calculate drawdown from peak"""
        if current_equity is None:
            current_equity = self.get_current_equity()
        
        if self.equity_peak == 0:
            return 0.0
        
        return (current_equity / self.equity_peak) - 1.0
    
    def calculate_efficiency_ratio(self):
        """
        Calculate efficiency ratio - measures if equity is trending or choppy
        
        Returns:
            float: Efficiency ratio (0.0 to 1.0)
        """
        if len(self.equity_curve) < self.efficiency_ratio_length + 1:
            return 0.0
        
        lookback_len = min(self.efficiency_ratio_length, len(self.equity_curve) - 1)
        start_idx = len(self.equity_curve) - lookback_len - 1
        end_idx = len(self.equity_curve) - 1
        
        net_change = abs(self.equity_curve[end_idx] - self.equity_curve[start_idx])
        
        volatility = 0.0
        for i in range(start_idx + 1, end_idx + 1):
            volatility += abs(self.equity_curve[i] - self.equity_curve[i - 1])
        
        if volatility == 0:
            return 0.0
        
        return max(0.0, min(1.0, net_change / volatility))
    
    def calculate_adaptive_sma_length(self, efficiency_ratio):
        """Calculate adaptive SMA length based on efficiency ratio"""
        adaptive_length = self.adaptive_sma_min + \
                         (self.adaptive_sma_max - self.adaptive_sma_min) * (1 - efficiency_ratio)
        return int(max(self.adaptive_sma_min, min(self.adaptive_sma_max, adaptive_length)))
    
    def calculate_adaptive_sma(self, sma_length):
        """Calculate simple moving average with adaptive length"""
        if len(self.equity_curve) < sma_length:
            return self.get_average_equity()
        return sum(self.equity_curve[-sma_length:]) / sma_length
    
    def calculate_confidence_multiplier(self, current_equity, adaptive_sma):
        """
        Calculate confidence multiplier using logistic curve
        
        Ranges from 0.5x to 1.5x (centered at 1.0x)
        - Above SMA → increase to max 1.5x
        - Below SMA → decrease to min 0.5x
        """
        if adaptive_sma == 0:
            return 1.0
        
        epsilon = 0.02
        distance_raw = (current_equity - adaptive_sma) / adaptive_sma
        distance = distance_raw if abs(distance_raw) > epsilon else 0.0
        
        # Sigmoid function
        confidence = 1.0 / (1.0 + math.exp(-4.0 * distance))
        
        # Map to 0.5 to 1.5 range (centered at 1.0)
        base_mult = 0.5 + 1.0 * confidence
        
        return max(0.5, min(1.5, base_mult))
    
    def get_equity_multiplier(self, current_equity, is_hyper_phase=False):
        """Calculate final equity-based position size multiplier"""
        if self.is_in_warmup():
            return {
                'multiplier': 1.0,
                'efficiency_ratio': 0.0,
                'sma_length': self.lookback_trades,
                'adaptive_sma': current_equity,
                'confidence': 1.0,
                'in_warmup': True
            }
        
        efficiency_ratio = self.calculate_efficiency_ratio()
        sma_length = self.calculate_adaptive_sma_length(efficiency_ratio)
        
        if is_hyper_phase:
            sma_length = int(sma_length * 0.8)
            sma_length = max(self.adaptive_sma_min, sma_length)
        
        adaptive_sma = self.calculate_adaptive_sma(sma_length)
        confidence = self.calculate_confidence_multiplier(current_equity, adaptive_sma)
        
        # In hyper phase, max 1.6x
        if is_hyper_phase and confidence > 1.0:
            confidence = 1.0 + (confidence - 1.0) * 1.2
            confidence = min(1.6, confidence)
        
        return {
            'multiplier': round(confidence, 3),
            'efficiency_ratio': round(efficiency_ratio, 3),
            'sma_length': sma_length,
            'adaptive_sma': round(adaptive_sma, 2),
            'confidence': round(confidence, 3),
            'in_warmup': False
        }
    
    def get_metrics(self):
        """Get comprehensive equity metrics for monitoring"""
        current = self.get_current_equity()
        average = self.get_average_equity()
        drawdown = self.calculate_drawdown(current)
        
        metrics = {
            'current_equity': round(current, 2),
            'average_equity': round(average, 2),
            'equity_peak': round(self.equity_peak, 2),
            'initial_equity': round(self.initial_equity, 2) if self.initial_equity else 0.0,
            'drawdown_pct': round(drawdown * 100, 2),
            'total_trades': self.total_trades,
            'in_warmup': self.is_in_warmup(),
            'curve_length': len(self.equity_curve),
            'consecutive_losses': self.consecutive_losses,
            'should_stop': self.should_stop_trading()
        }
        
        if not self.is_in_warmup():
            equity_mult = self.get_equity_multiplier(current)
            metrics.update({
                'efficiency_ratio': equity_mult['efficiency_ratio'],
                'adaptive_sma_length': equity_mult['sma_length'],
                'adaptive_sma': equity_mult['adaptive_sma'],
                'confidence_multiplier': equity_mult['confidence'],
                'equity_multiplier': equity_mult['multiplier']
            })
        
        return metrics
    
    def display_metrics(self):
        """Print formatted metrics display"""
        metrics = self.get_metrics()
        
        print(f"\n{'='*60}")
        print(f"📊 Karma Adaptive Equity Tracker Metrics")
        print(f"{'='*60}")
        print(f"Initial Equity:     ${metrics.get('initial_equity', 0):>10,.2f}")
        print(f"Current Equity:     ${metrics['current_equity']:>10,.2f}")
        print(f"Average Equity:     ${metrics['average_equity']:>10,.2f}")
        print(f"Peak Equity:        ${metrics['equity_peak']:>10,.2f}")
        print(f"Drawdown:           {metrics['drawdown_pct']:>10.2f}%")
        print(f"Total Trades:       {metrics['total_trades']:>10}")
        print(f"Consecutive Losses: {metrics['consecutive_losses']:>10}")
        print(f"In Warm-up:         {'Yes' if metrics['in_warmup'] else 'No':>10}")
        print(f"Should Stop:        {'⚠️ Yes' if metrics['should_stop'] else 'No':>10}")
        
        if not metrics['in_warmup']:
            print(f"\n📈 Adaptive Features:")
            print(f"Efficiency Ratio:   {metrics['efficiency_ratio']:>10.3f}")
            print(f"Adaptive SMA Len:   {metrics['adaptive_sma_length']:>10} trades")
            print(f"Adaptive SMA:       ${metrics['adaptive_sma']:>10,.2f}")
            print(f"Confidence Mult:    {metrics['confidence_multiplier']:>10.3f}x")
            print(f"Equity Multiplier:  {metrics['equity_multiplier']:>10.3f}x")
        
        print(f"{'='*60}\n")


class KarmaCompoundingStrategy:
    """
    🕉️ Karma's Fast Compounding Strategy with Adaptive Equity Tracking
    
    Intelligent position sizing that adapts to performance and market conditions.
    Works alongside signal generation strategies to optimize trade sizing.
    """
    
    def __init__(self, data_dir=None):
        """Initialize Karma Compounding Strategy"""
        self.name = "Karma Fast Compounding (AGR)"
        
        # Realistic parameters
        self.daily_target_percent = 0.75  # 0.75% daily ≈ 200% annual
        self.min_expected_move = 5.0
        self.min_confidence = 70
        
        # Risk parameters
        self.base_leverage = DEFAULT_LEVERAGE
        self.max_leverage = 25
        self.min_leverage = 10
        self.stop_loss_pct = STOP_LOSS_PERCENTAGE
        
        # Conservative multipliers
        self.peak_protect_multiplier = 0.60
        self.aggressive_multiplier = 1.15
        self.drawdown_threshold = 0.10
        
        # Maximum combined multiplier
        self.max_combined_multiplier = 1.5
        
        # Initialize adaptive equity tracker
        self.equity_tracker = AdaptiveEquityTracker(
            lookback_trades=21,
            warmup_trades=15,
            data_dir=data_dir
        )
        
        # Hyper-growth settings
        self.growth_target = 10.0  # 10x growth target
        
        # Daily tracking
        self.daily_profit = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
        # Load state
        self._load_state()
        
        print(f"🕉️ {self.name} initialized")
        print(f"   Daily Target: {self.daily_target_percent}%")
        print(f"   Max Combined Multiplier: {self.max_combined_multiplier}x")
        print(f"   Growth Target: {self.growth_target}x")
    
    def _load_state(self):
        """Load strategy state from disk"""
        state_file = self.equity_tracker.data_dir / "strategy_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    
                if state.get('date') == str(datetime.now().date()):
                    self.daily_profit = state.get('daily_profit', 0.0)
                    self.daily_trades = state.get('daily_trades', 0)
                
            except Exception as e:
                print(f"⚠️ Error loading strategy state: {e}")
    
    def _save_state(self):
        """Save strategy state to disk"""
        state_file = self.equity_tracker.data_dir / "strategy_state.json"
        try:
            state = {
                'date': str(datetime.now().date()),
                'daily_profit': self.daily_profit,
                'daily_trades': self.daily_trades,
                'last_update': datetime.now().isoformat()
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error saving strategy state: {e}")
    
    def _reset_daily_if_needed(self):
        """Reset daily counters if new day"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_profit = 0.0
            self.daily_trades = 0
            self.last_reset_date = current_date
            self._save_state()
    
    def is_hyper_phase(self, account_balance):
        """Dynamic hyper-phase detection based on actual starting equity"""
        initial = self.equity_tracker.initial_equity
        if initial is None or initial <= 0:
            return True
        
        target_equity = initial * self.growth_target
        return account_balance < target_equity
    
    def calculate_adaptive_leverage(self, account_balance, is_hyper_phase=False):
        """Calculate optimal leverage based on equity metrics"""
        leverage = self.base_leverage
        
        metrics = self.equity_tracker.get_metrics()
        
        if metrics['in_warmup']:
            return int(leverage)
        
        current = metrics['current_equity']
        average = metrics['average_equity']
        drawdown = metrics['drawdown_pct'] / 100
        
        if current > average * 1.05:
            leverage = min(leverage + 2, self.max_leverage)
        elif current < average * 0.95:
            leverage = max(leverage - 3, self.min_leverage)
        
        if drawdown < -0.15:
            leverage = max(leverage - 3, self.min_leverage)
        
        if is_hyper_phase and leverage < self.base_leverage:
            leverage = self.base_leverage
        
        return int(leverage)
    
    def calculate_risk_multiplier(self, account_balance, is_hyper_phase=False):
        """Calculate risk multiplier based on drawdown and peak protection"""
        drawdown = self.equity_tracker.calculate_drawdown(account_balance)
        
        if is_hyper_phase:
            if drawdown < -self.drawdown_threshold:
                return self.aggressive_multiplier
            return 1.0
        
        if drawdown < -self.drawdown_threshold:
            return self.aggressive_multiplier
        elif drawdown >= 0:
            return self.peak_protect_multiplier
        else:
            return 1.0
    
    def calculate_position_size(self, account_balance, expected_move_pct,
                                confidence_pct, is_hyper_phase=None):
        """
        Calculate position size with adaptive equity multiplier
        
        Returns dict with position sizing details and multipliers
        """
        if is_hyper_phase is None:
            is_hyper_phase = self.is_hyper_phase(account_balance)
        
        # Check circuit breaker
        if self.equity_tracker.should_stop_trading():
            return {
                'margin': 0,
                'notional': 0,
                'leverage': 0,
                'expected_profit': 0,
                'circuit_breaker': True,
                'reason': 'Circuit breaker triggered'
            }
        
        # Daily target
        daily_target = account_balance * (self.daily_target_percent / 100)
        remaining_target = max(daily_target - self.daily_profit, daily_target * 0.25)
        
        # Base position calculation
        base_position_notional = remaining_target / (expected_move_pct / 100)
        
        leverage = self.calculate_adaptive_leverage(account_balance, is_hyper_phase)
        margin_needed = base_position_notional / leverage
        
        confidence_multiplier = confidence_pct / 100.0
        
        equity_mult_data = self.equity_tracker.get_equity_multiplier(
            account_balance,
            is_hyper_phase
        )
        equity_multiplier = equity_mult_data['multiplier']
        
        risk_multiplier = self.calculate_risk_multiplier(account_balance, is_hyper_phase)
        
        progress_pct = (self.daily_profit / daily_target) * 100 if daily_target > 0 else 0
        
        if progress_pct >= 100:
            progress_multiplier = 0.0
        elif progress_pct >= 80:
            progress_multiplier = 0.5
        elif progress_pct < 30:
            progress_multiplier = 1.1
        else:
            progress_multiplier = 1.0
        
        # Calculate and CAP combined multiplier
        combined_mult = equity_multiplier * risk_multiplier * progress_multiplier
        combined_mult = max(0.5, min(self.max_combined_multiplier, combined_mult))
        
        final_margin = margin_needed * confidence_multiplier * combined_mult
        
        # Safety limits
        max_margin = account_balance * (MAX_POSITION_PERCENTAGE / 100)
        min_margin = 12.0 / leverage
        
        safe_margin = max(min_margin, min(final_margin, max_margin))
        final_notional = safe_margin * leverage
        
        return {
            'margin': round(safe_margin, 2),
            'notional': round(final_notional, 2),
            'leverage': leverage,
            'expected_profit': round(final_notional * (expected_move_pct / 100), 2),
            'daily_target': round(daily_target, 2),
            'remaining_target': round(remaining_target, 2),
            'progress_pct': round(progress_pct, 1),
            'confidence_multiplier': round(confidence_multiplier, 2),
            'equity_multiplier': round(equity_multiplier, 3),
            'risk_multiplier': round(risk_multiplier, 2),
            'progress_multiplier': round(progress_multiplier, 2),
            'combined_multiplier': round(combined_mult, 3),
            'equity_metrics': equity_mult_data,
            'circuit_breaker': False,
            'is_hyper_phase': is_hyper_phase
        }
    
    def record_trade_result(self, profit_usd, closing_equity):
        """Record completed trade result"""
        self.daily_profit += profit_usd
        self.daily_trades += 1
        
        self.equity_tracker.record_trade_close(closing_equity, profit_usd)
        self._save_state()
        
        print(f"\n📊 {self.name} - Trade #{self.daily_trades}")
        print(f"   P&L: ${profit_usd:+.2f}")
        print(f"   Daily Progress: ${self.daily_profit:.2f}")
        print(f"   Equity: ${closing_equity:.2f}")
        
        if not self.equity_tracker.is_in_warmup():
            metrics = self.equity_tracker.get_metrics()
            print(f"   Equity Multiplier: {metrics.get('equity_multiplier', 1.0):.3f}x")
        
        if self.equity_tracker.should_stop_trading():
            print(f"   ⚠️ Circuit Breaker Active - Consider stopping")
    
    def get_position_size_for_signal(self, account_balance, ai_confidence):
        """
        Convenience method for integration with trading system
        
        Args:
            account_balance: Current account equity
            ai_confidence: AI's confidence percentage (0-100)
            
        Returns:
            dict with 'notional', 'margin', 'leverage', or None if should not trade
        """
        self._reset_daily_if_needed()
        
        # Check circuit breaker
        if self.equity_tracker.should_stop_trading():
            print("🛑 Circuit breaker active - not sizing position")
            return None
        
        # Check daily limits
        daily_target = account_balance * (self.daily_target_percent / 100)
        progress_pct = (self.daily_profit / daily_target) * 100 if daily_target > 0 else 0
        
        if progress_pct >= 100:
            print("✅ Daily target met - not sizing position")
            return None
        
        if self.daily_trades >= 6:
            print("⚠️ Daily trade limit reached")
            return None
        
        if ai_confidence < self.min_confidence:
            print(f"⚠️ Confidence {ai_confidence}% below minimum {self.min_confidence}%")
            return None
        
        # Calculate position size
        sizing = self.calculate_position_size(
            account_balance=account_balance,
            expected_move_pct=self.min_expected_move,
            confidence_pct=ai_confidence
        )
        
        return sizing


# Create singleton instance
strategy = KarmaCompoundingStrategy()


# ============================================================================
# TEST SUITE
# ============================================================================

if __name__ == "__main__":
    """Test the Karma compounding strategy"""
    import tempfile
    
    print("\n" + "=" * 70)
    print("🕉️ Testing Karma Fast Compounding Strategy")
    print("=" * 70)
    
    # Use temp directory for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        strat = KarmaCompoundingStrategy(data_dir=tmp_dir)
        
        # Test 1: Verify multiplier range
        print("\n🧪 Test 1: Confidence Multiplier Range")
        tracker = strat.equity_tracker
        
        # Simulate some trades
        equity = 100.0
        for i in range(20):
            profit = 0.75 + (i * 0.1)
            equity += profit
            tracker.record_trade_close(equity, profit)
        
        # Test multiplier at various distances
        sma = tracker.calculate_adaptive_sma(8)
        
        test_cases = [
            (sma * 1.20, "+20% above SMA"),
            (sma * 1.10, "+10% above SMA"),
            (sma * 1.00, "At SMA"),
            (sma * 0.90, "-10% below SMA"),
            (sma * 0.80, "-20% below SMA"),
        ]
        
        print(f"   SMA: ${sma:.2f}")
        for test_equity, desc in test_cases:
            mult = tracker.calculate_confidence_multiplier(test_equity, sma)
            print(f"   {desc}: {mult:.3f}x")
        
        # Verify range
        assert tracker.calculate_confidence_multiplier(sma * 2, sma) <= 1.5, "Max should be 1.5"
        assert tracker.calculate_confidence_multiplier(sma * 0.5, sma) >= 0.5, "Min should be 0.5"
        print("   ✅ Multiplier range verified: 0.5x to 1.5x")
        
        # Test 2: Combined multiplier cap
        print("\n🧪 Test 2: Combined Multiplier Cap")
        sizing = strat.calculate_position_size(
            account_balance=equity,
            expected_move_pct=5.0,
            confidence_pct=90,
            is_hyper_phase=True
        )
        
        print(f"   Equity Mult: {sizing['equity_multiplier']:.3f}x")
        print(f"   Risk Mult: {sizing['risk_multiplier']:.2f}x")
        print(f"   Progress Mult: {sizing['progress_multiplier']:.2f}x")
        print(f"   Combined Mult: {sizing['combined_multiplier']:.3f}x")
        
        assert sizing['combined_multiplier'] <= 1.5, "Combined should be capped at 1.5"
        print("   ✅ Combined multiplier capped correctly")
        
        # Test 3: Circuit breaker
        print("\n🧪 Test 3: Circuit Breaker")
        
        # Simulate consecutive losses
        for i in range(5):
            equity -= 5
            tracker.record_trade_close(equity, -5.0)
        
        assert tracker.should_stop_trading(), "Should trigger circuit breaker"
        print(f"   Consecutive losses: {tracker.consecutive_losses}")
        print("   ✅ Circuit breaker triggered correctly")
        
        # Test 4: Warm-up period
        print("\n🧪 Test 4: Warm-up Period")
        
        fresh_tracker = AdaptiveEquityTracker(
            lookback_trades=21,
            warmup_trades=15,
            data_dir=tmp_dir + "/fresh"
        )
        
        for i in range(14):
            fresh_tracker.record_trade_close(100 + i)
        
        assert fresh_tracker.is_in_warmup(), "Should be in warmup at 14 trades"
        print(f"   At 14 trades: in_warmup = {fresh_tracker.is_in_warmup()}")
        
        fresh_tracker.record_trade_close(114)
        assert not fresh_tracker.is_in_warmup(), "Should exit warmup at 15 trades"
        print(f"   At 15 trades: in_warmup = {fresh_tracker.is_in_warmup()}")
        print("   ✅ Warm-up period correct (15 trades)")
        
        # Display final metrics
        strat.equity_tracker.display_metrics()
        
        print("\n" + "=" * 70)
        print("✅ All Tests Passed - Karma Strategy Ready")
        print("=" * 70 + "\n")
