"""
Three-Tier Position Close Validation System
============================================
Implements sophisticated decision-making for position closes.

Tier 0: Emergency Stop Loss (-2% or worse) - FORCE CLOSE
Tier 1: Profit Target (+0.5% or better) - AI decides
Tier 2: Age Gating (young positions < 1.5h need protection)
Tier 3: Mature Position Analysis with loss-adjusted confidence

Final Gate: Adjusted AI confidence must be >= 80% to close
"""

from typing import Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Stop Loss Threshold (Tier 0)
STOP_LOSS_THRESHOLD = -2.0  # Force close at -2% or worse

# Profit Target (Tier 1)
PROFIT_TARGET_THRESHOLD = 0.5  # AI can decide at +0.5% or better

# Age Thresholds (Tier 2)
YOUNG_POSITION_HOURS = 1.5  # Positions younger than this get special protection

# Loss Categories
SEVERE_LOSS_THRESHOLD = -1.2  # -2.0% to -1.2% = severe
MODERATE_LOSS_THRESHOLD = 0.0  # -1.2% to 0% = moderate

# Confidence Boosts
SEVERE_LOSS_BOOST = 25  # +25% confidence boost for severe losses
MODERATE_LOSS_BOOST = 15  # +15% confidence boost for moderate losses

# Final Gate
MIN_CONFIDENCE_TO_CLOSE = 80  # Must have 80% adjusted confidence to close


class CloseDecision(Enum):
    """Possible close decisions"""
    FORCE_CLOSE = "force_close"  # Stop loss triggered
    CLOSE = "close"  # AI recommended with sufficient confidence
    KEEP = "keep"  # Keep position open
    PROTECTED = "protected"  # Young position protected


@dataclass
class ValidationResult:
    """Result of close validation"""
    decision: CloseDecision
    reason: str
    original_confidence: float
    adjusted_confidence: float
    confidence_boost: float
    tier_triggered: int  # 0, 1, 2, or 3
    details: Dict


def validate_close_decision(
    symbol: str,
    pnl_percent: float,
    age_hours: float,
    ai_decision: str,
    ai_confidence: float
) -> ValidationResult:
    """
    Three-tier validation system for position close decisions.

    Args:
        symbol: Token symbol
        pnl_percent: Current P&L percentage (positive = profit, negative = loss)
        age_hours: Position age in hours
        ai_decision: AI's recommendation ("CLOSE" or "KEEP")
        ai_confidence: AI's confidence level (0-100)

    Returns:
        ValidationResult with final decision and reasoning
    """

    # Normalize AI decision
    ai_wants_close = ai_decision.upper() in ["CLOSE", "SELL", "EXIT"]

    # ========================================================================
    # TIER 0: EMERGENCY STOP LOSS
    # ========================================================================
    if pnl_percent <= STOP_LOSS_THRESHOLD:
        return ValidationResult(
            decision=CloseDecision.FORCE_CLOSE,
            reason=f"STOP LOSS: Position at {pnl_percent:.2f}% (threshold: {STOP_LOSS_THRESHOLD}%)",
            original_confidence=ai_confidence,
            adjusted_confidence=100.0,  # Forced
            confidence_boost=0,
            tier_triggered=0,
            details={
                "trigger": "stop_loss",
                "pnl": pnl_percent,
                "threshold": STOP_LOSS_THRESHOLD
            }
        )

    # ========================================================================
    # TIER 1: PROFIT TARGET ACHIEVEMENT
    # ========================================================================
    if pnl_percent >= PROFIT_TARGET_THRESHOLD:
        # AI is allowed to decide at profit target
        if ai_wants_close and ai_confidence >= MIN_CONFIDENCE_TO_CLOSE:
            return ValidationResult(
                decision=CloseDecision.CLOSE,
                reason=f"PROFIT TARGET: {pnl_percent:.2f}% profit, AI says CLOSE with {ai_confidence}% confidence",
                original_confidence=ai_confidence,
                adjusted_confidence=ai_confidence,  # No boost for profits
                confidence_boost=0,
                tier_triggered=1,
                details={
                    "trigger": "profit_target",
                    "pnl": pnl_percent,
                    "ai_decision": ai_decision
                }
            )
        else:
            return ValidationResult(
                decision=CloseDecision.KEEP,
                reason=f"PROFIT TARGET: {pnl_percent:.2f}% profit, but AI confidence {ai_confidence}% < {MIN_CONFIDENCE_TO_CLOSE}%",
                original_confidence=ai_confidence,
                adjusted_confidence=ai_confidence,
                confidence_boost=0,
                tier_triggered=1,
                details={
                    "trigger": "profit_target_low_confidence",
                    "pnl": pnl_percent,
                    "ai_decision": ai_decision
                }
            )

    # ========================================================================
    # TIER 2: YOUNG POSITION PROTECTION (< 1.5 hours)
    # ========================================================================
    if age_hours < YOUNG_POSITION_HOURS:
        # Young position - apply special rules

        # Scenario A: Severe loss (-2.0% to -1.2%)
        if pnl_percent <= SEVERE_LOSS_THRESHOLD:
            boost = SEVERE_LOSS_BOOST
            adjusted = min(100, ai_confidence + boost)

            if ai_wants_close and adjusted >= MIN_CONFIDENCE_TO_CLOSE:
                return ValidationResult(
                    decision=CloseDecision.CLOSE,
                    reason=f"YOUNG + SEVERE LOSS: {pnl_percent:.2f}%, age {age_hours:.1f}h, adjusted confidence {adjusted}%",
                    original_confidence=ai_confidence,
                    adjusted_confidence=adjusted,
                    confidence_boost=boost,
                    tier_triggered=2,
                    details={
                        "trigger": "young_severe_loss",
                        "loss_category": "severe",
                        "age": age_hours
                    }
                )
            else:
                return ValidationResult(
                    decision=CloseDecision.KEEP,
                    reason=f"YOUNG + SEVERE: {pnl_percent:.2f}%, but adjusted confidence {adjusted}% < {MIN_CONFIDENCE_TO_CLOSE}%",
                    original_confidence=ai_confidence,
                    adjusted_confidence=adjusted,
                    confidence_boost=boost,
                    tier_triggered=2,
                    details={
                        "trigger": "young_severe_loss_low_confidence",
                        "loss_category": "severe",
                        "age": age_hours
                    }
                )

        # Scenario B: Moderate loss (-1.2% to 0%)
        elif pnl_percent <= MODERATE_LOSS_THRESHOLD:
            boost = MODERATE_LOSS_BOOST
            adjusted = min(100, ai_confidence + boost)

            if ai_wants_close and adjusted >= MIN_CONFIDENCE_TO_CLOSE:
                return ValidationResult(
                    decision=CloseDecision.CLOSE,
                    reason=f"YOUNG + MODERATE LOSS: {pnl_percent:.2f}%, age {age_hours:.1f}h, adjusted confidence {adjusted}%",
                    original_confidence=ai_confidence,
                    adjusted_confidence=adjusted,
                    confidence_boost=boost,
                    tier_triggered=2,
                    details={
                        "trigger": "young_moderate_loss",
                        "loss_category": "moderate",
                        "age": age_hours
                    }
                )
            else:
                return ValidationResult(
                    decision=CloseDecision.KEEP,
                    reason=f"YOUNG + MODERATE: {pnl_percent:.2f}%, but adjusted confidence {adjusted}% < {MIN_CONFIDENCE_TO_CLOSE}%",
                    original_confidence=ai_confidence,
                    adjusted_confidence=adjusted,
                    confidence_boost=boost,
                    tier_triggered=2,
                    details={
                        "trigger": "young_moderate_loss_low_confidence",
                        "loss_category": "moderate",
                        "age": age_hours
                    }
                )

        # Scenario C: Small loss or break-even (> -1.2% to < +0.5%)
        else:
            # FORCE KEEP - too young with small loss
            return ValidationResult(
                decision=CloseDecision.PROTECTED,
                reason=f"PROTECTED: Young position ({age_hours:.1f}h), small loss {pnl_percent:.2f}% - let it develop",
                original_confidence=ai_confidence,
                adjusted_confidence=ai_confidence,
                confidence_boost=0,
                tier_triggered=2,
                details={
                    "trigger": "young_protected",
                    "loss_category": "small",
                    "age": age_hours
                }
            )

    # ========================================================================
    # TIER 3: MATURE POSITION ANALYSIS (>= 1.5 hours)
    # ========================================================================

    # Scenario A: Severe loss (-2.0% to -1.2%)
    if pnl_percent <= SEVERE_LOSS_THRESHOLD:
        boost = SEVERE_LOSS_BOOST
        adjusted = min(100, ai_confidence + boost)

        if ai_wants_close and adjusted >= MIN_CONFIDENCE_TO_CLOSE:
            return ValidationResult(
                decision=CloseDecision.CLOSE,
                reason=f"MATURE + SEVERE LOSS: {pnl_percent:.2f}%, age {age_hours:.1f}h, adjusted confidence {adjusted}%",
                original_confidence=ai_confidence,
                adjusted_confidence=adjusted,
                confidence_boost=boost,
                tier_triggered=3,
                details={
                    "trigger": "mature_severe_loss",
                    "loss_category": "severe",
                    "age": age_hours
                }
            )
        else:
            return ValidationResult(
                decision=CloseDecision.KEEP,
                reason=f"MATURE + SEVERE: {pnl_percent:.2f}%, but adjusted confidence {adjusted}% < {MIN_CONFIDENCE_TO_CLOSE}%",
                original_confidence=ai_confidence,
                adjusted_confidence=adjusted,
                confidence_boost=boost,
                tier_triggered=3,
                details={
                    "trigger": "mature_severe_loss_low_confidence",
                    "loss_category": "severe",
                    "age": age_hours
                }
            )

    # Scenario B: Moderate loss (-1.2% to 0%)
    elif pnl_percent <= MODERATE_LOSS_THRESHOLD:
        boost = MODERATE_LOSS_BOOST
        adjusted = min(100, ai_confidence + boost)

        if ai_wants_close and adjusted >= MIN_CONFIDENCE_TO_CLOSE:
            return ValidationResult(
                decision=CloseDecision.CLOSE,
                reason=f"MATURE + MODERATE LOSS: {pnl_percent:.2f}%, age {age_hours:.1f}h, adjusted confidence {adjusted}%",
                original_confidence=ai_confidence,
                adjusted_confidence=adjusted,
                confidence_boost=boost,
                tier_triggered=3,
                details={
                    "trigger": "mature_moderate_loss",
                    "loss_category": "moderate",
                    "age": age_hours
                }
            )
        else:
            return ValidationResult(
                decision=CloseDecision.KEEP,
                reason=f"MATURE + MODERATE: {pnl_percent:.2f}%, but adjusted confidence {adjusted}% < {MIN_CONFIDENCE_TO_CLOSE}%",
                original_confidence=ai_confidence,
                adjusted_confidence=adjusted,
                confidence_boost=boost,
                tier_triggered=3,
                details={
                    "trigger": "mature_moderate_loss_low_confidence",
                    "loss_category": "moderate",
                    "age": age_hours
                }
            )

    # Scenario C: Small loss or break-even (> -1.2% to < +0.5%)
    else:
        # No boost for small losses on mature positions
        if ai_wants_close and ai_confidence >= MIN_CONFIDENCE_TO_CLOSE:
            return ValidationResult(
                decision=CloseDecision.CLOSE,
                reason=f"MATURE + SMALL LOSS: {pnl_percent:.2f}%, AI confident at {ai_confidence}%",
                original_confidence=ai_confidence,
                adjusted_confidence=ai_confidence,
                confidence_boost=0,
                tier_triggered=3,
                details={
                    "trigger": "mature_small_loss",
                    "loss_category": "small",
                    "age": age_hours
                }
            )
        else:
            return ValidationResult(
                decision=CloseDecision.KEEP,
                reason=f"MATURE + SMALL: {pnl_percent:.2f}%, AI confidence {ai_confidence}% < {MIN_CONFIDENCE_TO_CLOSE}% - let it evolve",
                original_confidence=ai_confidence,
                adjusted_confidence=ai_confidence,
                confidence_boost=0,
                tier_triggered=3,
                details={
                    "trigger": "mature_small_loss_low_confidence",
                    "loss_category": "small",
                    "age": age_hours
                }
            )


def format_validation_result(result: ValidationResult) -> str:
    """Format validation result for logging"""
    lines = [
        f"Decision: {result.decision.value.upper()}",
        f"Reason: {result.reason}",
        f"Tier: {result.tier_triggered}",
        f"Confidence: {result.original_confidence}% → {result.adjusted_confidence}% (boost: +{result.confidence_boost}%)"
    ]
    return "\n".join(lines)
