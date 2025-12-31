"""
Intelligence Integrator
========================
Collects and integrates signals from Strategy Agent and Volume Agent
to provide enhanced context for trading decisions.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

try:
    from termcolor import cprint
except ImportError:
    def cprint(msg, *args, **kwargs):
        print(msg)


# Data paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
VOLUME_ANALYSIS_LOG = PROJECT_ROOT / "src" / "data" / "volume_agent" / "agent_analysis.jsonl"


# ============================================================================
# STRATEGY AGENT INTEGRATION
# ============================================================================

def get_strategy_signals(token: str, strategy_agent=None) -> Optional[Dict]:
    """
    Get strategy signals for a token.

    Args:
        token: Token symbol
        strategy_agent: Initialized StrategyAgent instance

    Returns:
        Dict with strategy signals or None
    """
    if strategy_agent is None:
        return None

    try:
        signals = strategy_agent.get_signals(token)

        if not signals:
            return None

        # Format signals for AI context
        formatted = {
            "token": token,
            "signals": [],
            "summary": ""
        }

        for signal in signals:
            formatted["signals"].append({
                "strategy": signal.get("strategy_name", "Unknown"),
                "direction": signal.get("direction", "NOTHING"),
                "strength": signal.get("signal", 0),
                "metadata": signal.get("metadata", {})
            })

        # Create summary
        buy_signals = [s for s in signals if s.get("direction") == "BUY"]
        sell_signals = [s for s in signals if s.get("direction") == "SELL"]

        if buy_signals:
            avg_strength = sum(s.get("signal", 0) for s in buy_signals) / len(buy_signals)
            formatted["summary"] = f"BUY signals from {len(buy_signals)} strategies (avg strength: {avg_strength:.0%})"
        elif sell_signals:
            avg_strength = sum(s.get("signal", 0) for s in sell_signals) / len(sell_signals)
            formatted["summary"] = f"SELL signals from {len(sell_signals)} strategies (avg strength: {avg_strength:.0%})"
        else:
            formatted["summary"] = "No actionable strategy signals"

        return formatted

    except Exception as e:
        cprint(f"⚠️ Error getting strategy signals for {token}: {e}", "yellow")
        return None


def format_strategy_signals_for_ai(signals: Dict) -> str:
    """Format strategy signals as context string for AI prompt."""
    if not signals or not signals.get("signals"):
        return "No strategy signals available."

    lines = [f"Token: {signals['token']}", f"Summary: {signals['summary']}", "Signals:"]

    for signal in signals["signals"]:
        direction = signal.get("direction", "NOTHING")
        strength = signal.get("strength", 0)
        strategy = signal.get("strategy", "Unknown")
        lines.append(f"  - {strategy}: {direction} ({strength:.0%} strength)")

    return "\n".join(lines)


# ============================================================================
# VOLUME AGENT INTEGRATION
# ============================================================================

def get_latest_volume_analysis() -> Optional[Dict]:
    """
    Read the latest volume agent analysis from JSONL log.

    Returns:
        Latest analysis entry or None
    """
    try:
        if not VOLUME_ANALYSIS_LOG.exists():
            return None

        # Read the last line of JSONL file
        latest = None
        with open(VOLUME_ANALYSIS_LOG, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        latest = json.loads(line)
                    except json.JSONDecodeError:
                        continue

        return latest

    except Exception as e:
        cprint(f"⚠️ Error reading volume analysis: {e}", "yellow")
        return None


def get_volume_intel_for_token(token: str, max_age_hours: float = 8) -> Optional[Dict]:
    """
    Get volume intelligence for a specific token.

    Args:
        token: Token symbol
        max_age_hours: Maximum age of data to consider

    Returns:
        Volume intel dict or None
    """
    try:
        latest = get_latest_volume_analysis()

        if not latest:
            return None

        # Check data freshness
        timestamp = latest.get("timestamp", 0)
        age_hours = (datetime.now().timestamp() - timestamp) / 3600

        if age_hours > max_age_hours:
            cprint(f"⚠️ Volume data is {age_hours:.1f}h old (max: {max_age_hours}h)", "yellow")
            return None

        # Find token in changes
        changes = latest.get("changes", [])
        for change in changes:
            if change.get("symbol", "").upper() == token.upper():
                return {
                    "symbol": token,
                    "rank": change.get("current_rank", 0),
                    "volume_24h": change.get("current_volume", 0),
                    "volume_change_4h": change.get("volume_change_4h"),
                    "volume_change_24h": change.get("volume_change_24h"),
                    "rank_change_4h": change.get("rank_change_4h"),
                    "is_new_entry": change.get("is_new_entry", False),
                    "price_change_24h": change.get("change_24h", 0),
                    "funding_rate": change.get("funding_rate", 0),
                    "open_interest": change.get("open_interest", 0),
                    "data_age_hours": age_hours
                }

        return None

    except Exception as e:
        cprint(f"⚠️ Error getting volume intel for {token}: {e}", "yellow")
        return None


def format_volume_intel_for_ai(intel: Dict) -> str:
    """Format volume intelligence as context string for AI prompt."""
    if not intel:
        return "No volume intelligence available."

    lines = [f"Token: {intel['symbol']}", f"Current Rank: #{intel['rank']}"]

    # Volume info
    vol_24h = intel.get("volume_24h", 0)
    if vol_24h >= 1_000_000_000:
        vol_str = f"${vol_24h/1_000_000_000:.2f}B"
    elif vol_24h >= 1_000_000:
        vol_str = f"${vol_24h/1_000_000:.2f}M"
    else:
        vol_str = f"${vol_24h/1_000:.2f}K"
    lines.append(f"24H Volume: {vol_str}")

    # Volume changes
    if intel.get("volume_change_4h") is not None:
        lines.append(f"4H Volume Change: {intel['volume_change_4h']:+.1f}%")
    if intel.get("volume_change_24h") is not None:
        lines.append(f"24H Volume Change: {intel['volume_change_24h']:+.1f}%")

    # Rank movement
    if intel.get("rank_change_4h") is not None:
        rank_change = intel["rank_change_4h"]
        if rank_change > 0:
            lines.append(f"Rank Movement: ↑ Climbed {rank_change} spots")
        elif rank_change < 0:
            lines.append(f"Rank Movement: ↓ Dropped {abs(rank_change)} spots")
        else:
            lines.append("Rank Movement: Stable")

    if intel.get("is_new_entry"):
        lines.append("Status: NEW ENTRY to top rankings!")

    # Additional metrics
    if intel.get("funding_rate"):
        lines.append(f"Funding Rate: {intel['funding_rate']:.4f}%")
    if intel.get("open_interest"):
        oi = intel["open_interest"]
        if oi >= 1_000_000:
            oi_str = f"${oi/1_000_000:.2f}M"
        else:
            oi_str = f"${oi/1_000:.2f}K"
        lines.append(f"Open Interest: {oi_str}")

    lines.append(f"Data Age: {intel.get('data_age_hours', 0):.1f}h ago")

    return "\n".join(lines)


def get_volume_summary() -> str:
    """Get a summary of the latest volume analysis for all top tokens."""
    try:
        latest = get_latest_volume_analysis()

        if not latest:
            return "No volume analysis data available."

        changes = latest.get("changes", [])
        if not changes:
            return "No token data in volume analysis."

        # Identify notable patterns
        new_entries = [c for c in changes if c.get("is_new_entry")]
        vol_accelerators = [c for c in changes if c.get("volume_change_4h") and c["volume_change_4h"] > 50]
        climbers = [c for c in changes if c.get("rank_change_4h") and c["rank_change_4h"] >= 3]

        lines = ["Volume Analysis Summary:"]

        if new_entries:
            symbols = ", ".join(c["symbol"] for c in new_entries)
            lines.append(f"  🆕 New Top-15 Entries: {symbols}")

        if vol_accelerators:
            details = ", ".join(f"{c['symbol']} (+{c['volume_change_4h']:.0f}%)" for c in vol_accelerators)
            lines.append(f"  🔥 Volume Accelerators (>50%): {details}")

        if climbers:
            details = ", ".join(f"{c['symbol']} (↑{c['rank_change_4h']})" for c in climbers)
            lines.append(f"  ⬆️ Rank Climbers: {details}")

        if not (new_entries or vol_accelerators or climbers):
            lines.append("  ✅ Market steady - no major volume signals")

        # Add swarm recommendation if available
        swarm_result = latest.get("swarm_result", {})
        consensus = swarm_result.get("consensus_summary", "")
        if consensus:
            lines.append(f"  🧠 Swarm Consensus: {consensus[:200]}...")

        return "\n".join(lines)

    except Exception as e:
        return f"Error getting volume summary: {str(e)}"


# ============================================================================
# COMBINED INTELLIGENCE
# ============================================================================

def collect_all_intelligence(
    token: str,
    strategy_agent=None,
    include_volume: bool = True
) -> Dict:
    """
    Collect all available intelligence for a token.

    Args:
        token: Token symbol
        strategy_agent: Initialized StrategyAgent (optional)
        include_volume: Whether to include volume data

    Returns:
        Dict with all intelligence sources
    """
    intel = {
        "token": token,
        "strategy_signals": None,
        "volume_intel": None,
        "combined_context": ""
    }

    # Collect strategy signals
    if strategy_agent:
        strategy_signals = get_strategy_signals(token, strategy_agent)
        if strategy_signals:
            intel["strategy_signals"] = strategy_signals

    # Collect volume intelligence
    if include_volume:
        volume_intel = get_volume_intel_for_token(token)
        if volume_intel:
            intel["volume_intel"] = volume_intel

    # Build combined context string
    context_parts = []

    if intel["strategy_signals"]:
        context_parts.append("=== STRATEGY SIGNALS ===")
        context_parts.append(format_strategy_signals_for_ai(intel["strategy_signals"]))

    if intel["volume_intel"]:
        context_parts.append("=== VOLUME INTELLIGENCE ===")
        context_parts.append(format_volume_intel_for_ai(intel["volume_intel"]))

    intel["combined_context"] = "\n\n".join(context_parts) if context_parts else ""

    return intel
