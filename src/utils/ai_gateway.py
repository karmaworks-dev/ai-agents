"""
Unified AI Analysis Gateway
============================
Provides a single interface for AI model queries (single or swarm mode).
Returns standardized structured output for all AI calls.
"""

import json
import re
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

try:
    from termcolor import cprint
except ImportError:
    def cprint(msg, *args, **kwargs):
        print(msg)


class AIDecision(Enum):
    """Possible AI decisions"""
    BUY = "BUY"
    SELL = "SELL"
    NOTHING = "NOTHING"
    KEEP = "KEEP"
    CLOSE = "CLOSE"


@dataclass
class AIResponse:
    """Standardized AI response structure"""
    decision: str  # BUY, SELL, NOTHING, KEEP, CLOSE
    confidence: float  # 0-100
    reasoning: str
    raw_response: str
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict] = None


def extract_json_from_text(text: str) -> Optional[Dict]:
    """Safely extract JSON object from AI model responses containing text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


def parse_ai_response(raw_response: str, default_decision: str = "NOTHING") -> AIResponse:
    """
    Parse AI response into structured format.

    Attempts to extract:
    - decision: BUY/SELL/NOTHING/KEEP/CLOSE
    - confidence: 0-100 number
    - reasoning: explanation text
    """
    try:
        # Try to parse as JSON first
        json_data = extract_json_from_text(raw_response)

        if json_data:
            # Extract decision
            decision = json_data.get("decision", json_data.get("action", default_decision))
            if isinstance(decision, str):
                decision = decision.upper().strip()

            # Extract confidence
            confidence = json_data.get("confidence", 50)
            if isinstance(confidence, str):
                # Handle percentage strings like "75%"
                confidence = float(confidence.replace("%", "").strip())
            confidence = max(0, min(100, float(confidence)))

            # Extract reasoning
            reasoning = json_data.get("reasoning", json_data.get("reason", "No reasoning provided"))

            return AIResponse(
                decision=decision,
                confidence=confidence,
                reasoning=str(reasoning),
                raw_response=raw_response,
                success=True,
                metadata=json_data
            )

        # Fallback: Parse text response
        response_upper = raw_response.upper()

        # Detect decision from text
        if "BUY" in response_upper and "DO NOT BUY" not in response_upper and "DON'T BUY" not in response_upper:
            decision = "BUY"
        elif "SELL" in response_upper or "CLOSE" in response_upper:
            decision = "SELL"
        elif "KEEP" in response_upper or "HOLD" in response_upper:
            decision = "KEEP"
        else:
            decision = default_decision

        # Try to extract confidence from text
        confidence = 50  # Default
        confidence_match = re.search(r'(\d{1,3})\s*%', raw_response)
        if confidence_match:
            confidence = min(100, max(0, int(confidence_match.group(1))))

        # Try to find confidence keywords
        if "high confidence" in raw_response.lower() or "very confident" in raw_response.lower():
            confidence = max(confidence, 85)
        elif "moderate confidence" in raw_response.lower():
            confidence = max(confidence, 65)
        elif "low confidence" in raw_response.lower():
            confidence = min(confidence, 40)

        return AIResponse(
            decision=decision,
            confidence=confidence,
            reasoning=raw_response[:500],  # Truncate for reasoning
            raw_response=raw_response,
            success=True
        )

    except Exception as e:
        return AIResponse(
            decision=default_decision,
            confidence=50,
            reasoning=f"Failed to parse AI response: {str(e)}",
            raw_response=raw_response,
            success=False,
            error=str(e)
        )


def query_single_model(
    prompt: str,
    model_factory,
    provider: str = "anthropic",
    temperature: float = 0.3,
    max_tokens: int = 1000
) -> AIResponse:
    """
    Query a single AI model.

    Args:
        prompt: The prompt to send
        model_factory: The model factory module
        provider: AI provider (anthropic, openai, deepseek, etc.)
        temperature: Model temperature
        max_tokens: Max response tokens

    Returns:
        AIResponse with structured output
    """
    try:
        model = model_factory.ModelFactory.create_model(provider)
        response = model.generate_response(
            system_prompt="You are a trading analysis AI. Always respond with valid JSON.",
            user_content=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return parse_ai_response(response)

    except Exception as e:
        cprint(f"❌ Single model query failed: {e}", "red")
        return AIResponse(
            decision="NOTHING",
            confidence=0,
            reasoning=f"Model query failed: {str(e)}",
            raw_response="",
            success=False,
            error=str(e)
        )


def query_swarm(
    prompt: str,
    swarm_agent
) -> AIResponse:
    """
    Query the AI swarm for consensus.

    Args:
        prompt: The prompt to send
        swarm_agent: Initialized SwarmAgent instance

    Returns:
        AIResponse with consensus result
    """
    try:
        result = swarm_agent.query(prompt)

        if not result:
            return AIResponse(
                decision="NOTHING",
                confidence=0,
                reasoning="Swarm returned no result",
                raw_response="",
                success=False,
                error="Empty swarm result"
            )

        # Extract consensus from swarm result
        consensus = result.get("consensus_summary", "")
        metadata = result.get("metadata", {})

        # Parse the consensus
        parsed = parse_ai_response(consensus)
        parsed.metadata = result
        parsed.raw_response = json.dumps(result, default=str)

        return parsed

    except Exception as e:
        cprint(f"❌ Swarm query failed: {e}", "red")
        return AIResponse(
            decision="NOTHING",
            confidence=0,
            reasoning=f"Swarm query failed: {str(e)}",
            raw_response="",
            success=False,
            error=str(e)
        )


def analyze_with_ai(
    prompt: str,
    use_swarm: bool = False,
    model_factory=None,
    swarm_agent=None,
    provider: str = "anthropic",
    default_decision: str = "NOTHING"
) -> AIResponse:
    """
    Unified AI analysis gateway.

    Routes to single model or swarm based on configuration.

    Args:
        prompt: Analysis prompt
        use_swarm: Whether to use swarm mode
        model_factory: Model factory for single model mode
        swarm_agent: SwarmAgent for swarm mode
        provider: AI provider for single model
        default_decision: Default if analysis fails

    Returns:
        AIResponse with structured output
    """
    try:
        if use_swarm and swarm_agent is not None:
            cprint("♾️ Using Swarm Mode for analysis...", "cyan")
            return query_swarm(prompt, swarm_agent)
        elif model_factory is not None:
            cprint("🧠 Using Single Model for analysis...", "cyan")
            return query_single_model(prompt, model_factory, provider)
        else:
            return AIResponse(
                decision=default_decision,
                confidence=0,
                reasoning="No AI model configured",
                raw_response="",
                success=False,
                error="No model_factory or swarm_agent provided"
            )

    except Exception as e:
        cprint(f"❌ AI analysis failed: {e}", "red")
        return AIResponse(
            decision=default_decision,
            confidence=0,
            reasoning=f"Analysis failed: {str(e)}",
            raw_response="",
            success=False,
            error=str(e)
        )


# ============================================================================
# ENHANCED PROMPTS FOR STRUCTURED OUTPUT
# ============================================================================

POSITION_ANALYSIS_PROMPT = """You are a trading position analyst. Analyze the following position and market data.

POSITION DETAILS:
{position_info}

MARKET DATA:
{market_data}

{additional_context}

IMPORTANT:
- Your confidence percentage (0-100) is CRITICAL for the decision system
- Be honest about uncertainty - the system will apply additional validation
- Consider technical indicators, price action, and trend strength

Respond with ONLY valid JSON in this exact format:
{{
    "decision": "KEEP" or "CLOSE",
    "confidence": <number 0-100>,
    "reasoning": "<brief explanation of your analysis>"
}}"""


ENTRY_ANALYSIS_PROMPT = """You are a trading entry analyst. Analyze the following market data for potential entry.

TOKEN: {symbol}

MARKET DATA:
{market_data}

{additional_context}

IMPORTANT:
- Your confidence percentage (0-100) is CRITICAL for the decision system
- Consider technical indicators, trend strength, support/resistance
- Only recommend BUY if you see a clear opportunity

Respond with ONLY valid JSON in this exact format:
{{
    "decision": "BUY" or "SELL" or "NOTHING",
    "confidence": <number 0-100>,
    "reasoning": "<brief explanation of your analysis>"
}}"""


def format_position_prompt(
    position_info: Dict,
    market_data: str,
    strategy_signals: Optional[str] = None,
    volume_intel: Optional[str] = None
) -> str:
    """Format the position analysis prompt with all context."""
    additional_parts = []

    if strategy_signals:
        additional_parts.append(f"STRATEGY SIGNALS:\n{strategy_signals}")

    if volume_intel:
        additional_parts.append(f"VOLUME INTELLIGENCE:\n{volume_intel}")

    additional_context = "\n\n".join(additional_parts) if additional_parts else ""

    return POSITION_ANALYSIS_PROMPT.format(
        position_info=json.dumps(position_info, indent=2),
        market_data=market_data,
        additional_context=additional_context
    )


def format_entry_prompt(
    symbol: str,
    market_data: str,
    strategy_signals: Optional[str] = None,
    volume_intel: Optional[str] = None
) -> str:
    """Format the entry analysis prompt with all context."""
    additional_parts = []

    if strategy_signals:
        additional_parts.append(f"STRATEGY SIGNALS:\n{strategy_signals}")

    if volume_intel:
        additional_parts.append(f"VOLUME INTELLIGENCE:\n{volume_intel}")

    additional_context = "\n\n".join(additional_parts) if additional_parts else ""

    return ENTRY_ANALYSIS_PROMPT.format(
        symbol=symbol,
        market_data=market_data,
        additional_context=additional_context
    )
