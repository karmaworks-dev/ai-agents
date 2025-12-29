"""
🌙  LLM Trading Agent 🌙

DUAL-MODE AI TRADING SYSTEM:

🤖 SINGLE MODEL MODE (Fast - ~10 seconds per token):
   - Uses one AI model for quick trading decisions
   - Best for: Fast execution, high-frequency strategies
   - Configure model in config.py: AI_MODEL_TYPE and AI_MODEL_NAME

🌊 SWARM MODE (Consensus - ~45-60 seconds per token):
   - Queries 6 AI models simultaneously for consensus voting
   - Models vote: "Buy", "Sell", or "Do Nothing"
   - Majority decision wins with confidence percentage
   - Best for: Higher confidence trades, 15-minute+ timeframes
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re

# 🔧 Import dashboard logging helper from trading_app
try:
    from trading_app import add_console_log
except Exception:
    def add_console_log(message, level="info"):
        print(f"[{level.upper()}] {message}")

def log_and_print(message, level="info"):
    """Show message in terminal and dashboard console"""
    print(message, flush=True)
    try:
        add_console_log(message, level)
    except Exception:
        pass


def extract_json_from_text(text):
    """Safely extract JSON object from AI model responses containing text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            print("⚠️ JSON extraction failed even after matching braces.")
            return None
    print("⚠️ No JSON object found in AI response.")
    return None


# ============================================================================
# 🚨 CRITICAL: THIS MUST BE HERE (BEFORE 'src' IMPORTS)
# ============================================================================
# Add project root to path so Python can find 'src'
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)
# ============================================================================

# 👇 NOW you can import from src safely
from src.models import model_factory
from src.agents.swarm_agent import SwarmAgent 
from src.data.ohlcv_collector import collect_all_tokens


# Load Environment Variables
load_dotenv()

# ============================================================================
# 🔧 OPTIONAL: COLOR PRINT & PANDAS SHIM (Keep your existing helpers)
# ============================================================================
try:
    from termcolor import cprint
except Exception:
    def cprint(msg, *args, **kwargs):
        print(msg)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except Exception as e:
    pd = None
    PANDAS_AVAILABLE = False
    cprint(f"⚠️ pandas not installed: {e}. Using lightweight DataFrame shim.", "yellow")
    import types

    class SimpleDataFrame:
        def __init__(self, data=None, columns=None):
            self._data = list(data) if data else []
            if columns:
                self.columns = list(columns)
            else:
                self.columns = list(self._data[0].keys()) if self._data else []
            self.index = list(range(len(self._data)))

        def __len__(self):
            return len(self._data)

        def head(self, n=5):
            return SimpleDataFrame(self._data[:n], columns=self.columns)

        def tail(self, n=3):
            return SimpleDataFrame(self._data[-n:], columns=self.columns)

        def to_string(self):
            if not self._data:
                return "<empty DataFrame>"
            header = " | ".join(self.columns)
            lines = [header]
            for row in self._data:
                lines.append(" | ".join(str(row.get(c, "")) for c in self.columns))
            return "\n".join(lines)

        def __str__(self):
            return self.to_string()

        def to_dict(self):
            return self._data

    def _concat(dfs, ignore_index=True):
        rows = []
        cols = []
        for df in dfs:
            if isinstance(df, SimpleDataFrame):
                rows.extend(df._data)
                for c in df.columns:
                    if c not in cols:
                        cols.append(c)
            elif isinstance(df, dict):
                rows.append(df)
        return SimpleDataFrame(rows, columns=cols)

    pd = types.SimpleNamespace(DataFrame=SimpleDataFrame, concat=_concat)

# ============================================================================
# 🔧 TRADING AGENT CONFIGURATION
# ============================================================================
from eth_account import Account

# 🦈 EXCHANGE SELECTION
EXCHANGE = "HYPERLIQUID"  # Options: "ASTER", "HYPERLIQUID", "SOLANA"

# 🌊 AI MODE SELECTION
USE_SWARM_MODE = False # True = Swarm Mode (all Models), False = Single Model

# 📈 TRADING MODE SETTINGS
LONG_ONLY = False 

# 🤖 SINGLE MODEL SETTINGS
AI_MODEL_TYPE = 'gemini' 
AI_MODEL_NAME = 'gemini-2.5-pro'  # Fast Gemini 2.5 model
AI_TEMPERATURE = 0.6   
AI_MAX_TOKENS = 3000   

# 💰 POSITION SIZING & RISK MANAGEMENT
USE_PORTFOLIO_ALLOCATION = True 
MAX_POSITION_PERCENTAGE = 90      
LEVERAGE = 20                     

# Stop Loss & Take Profit
STOP_LOSS_PERCENTAGE = 2.0      # SL @ -2% PnL
TAKE_PROFIT_PERCENTAGE = 5.0    # TP @ +5% PnL 
PNL_CHECK_INTERVAL = 5          # check PnL every 5 minutes          

# Legacy settings 
usd_size = 25                  
max_usd_order_size = 3           
CASH_PERCENTAGE = 10

# 📊 MARKET DATA COLLECTION
DAYSBACK_4_DATA = 2              
DATA_TIMEFRAME = '30m'            
SAVE_OHLCV_DATA = False          

# ⚡ TRADING EXECUTION SETTINGS
slippage = 199                   
SLEEP_BETWEEN_RUNS_MINUTES = 60  

# 🎯 TOKEN CONFIGURATION
address = "ACCOUNT_ADDRESS" 

# For SOLANA exchange
USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" 
SOL_ADDRESS = "So11111111111111111111111111111111111111111"    
EXCLUDED_TOKENS = [USDC_ADDRESS, SOL_ADDRESS]

MONITORED_TOKENS = []

# For ASTER/HYPERLIQUID exchanges
SYMBOLS = [
    'ETH',        # Ethereum
    'BTC',        # Bitcoin
    'SOL',        # Solana
    'AAVE',       # Aave
    'LINK',       # Chainlink
    'LTC',        # Litecoin
    'FARTCOIN',   # FartCoin (for the fun)
]

# ============================================================================
# 🔌 EXCHANGE IMPORTS
# ============================================================================
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Corrected Import Logic
if EXCHANGE == "ASTER":
    try:
        from src import nice_funcs_aster as n
        cprint("🦈 Exchange: Aster DEX (Futures)", "cyan", attrs=['bold'])
    except ImportError:
        cprint("❌ Error: nice_funcs_aster not found", "red")
        
elif EXCHANGE == "HYPERLIQUID":
    try:
        import nice_funcs_hyperliquid as n
        cprint("🦈 Exchange: HyperLiquid (Perpetuals) - Using local nice_funcs_hyperliquid.py", "cyan", attrs=['bold'])
    except ImportError:
        try:
            from src import nice_funcs_hyperliquid as n
            cprint("🦈 Exchange: HyperLiquid (Perpetuals) - Using src module", "cyan", attrs=['bold'])
        except ImportError:
            cprint("❌ Error: nice_funcs_hyperliquid.py not found! Ensure it is in the same folder.", "red")
            sys.exit(1)
            
elif EXCHANGE == "SOLANA":
    try:
        from src import nice_funcs as n
        cprint("🦈 Exchange: Solana (On-chain DEX)", "cyan", attrs=['bold'])
    except ImportError:
        cprint("❌ Error: Solana functions not found", "red")

else:
    cprint(f"❌ Unknown exchange: {EXCHANGE}", "red")
    cprint("Available exchanges: ASTER, HYPERLIQUID, SOLANA", "yellow")
    sys.exit(1)

from src.data.ohlcv_collector import collect_all_tokens

# ============================================================================
# PROMPTS
# ============================================================================

TRADING_PROMPT = """
You are a renowned crypto trading expert and Trading Assistant

Analyze the provided market data, CURRENT POSITION, and STRATEGY CONTEXT signals to make a trading decision.

{position_context}

Market Data Criteria:
1. Price action relative to MA20 and MA40
2. RSI levels and trend
3. Volume patterns
4. Recent price movements

{strategy_context}

Respond in this exact format:
1. First line must be one of: BUY, SELL, or NOTHING (in caps)
2. Then explain your reasoning, always including:
   - Technical analysis
   - Strategy signals analysis (if available)
   - Risk factors
   - Market conditions
   - Confidence level (as a percentage, e.g. 75%)

Remember: 
- Always prioritizes risk management! 🛡️
- Never trade USDC or SOL directly
- Consider both technical and strategy signals
"""

ALLOCATION_PROMPT = """
You are our Portfolio Allocation Assistant 🌙

Given the total portfolio size and trading recommendations, allocate capital efficiently.
Consider:
1. Position sizing based on confidence levels
2. Risk distribution
3. Keep cash buffer as specified
4. Maximum allocation per position

Format your response as a Python dictionary:
{
    "token_address": allocated_amount,  # In USD
    ...
    "USDC_ADDRESS": remaining_cash  # Always use USDC_ADDRESS for cash
}

Remember:
- Total allocations must not exceed total_size
- Higher confidence should get larger allocations
- Never allocate more than {MAX_POSITION_PERCENTAGE}% to a single position
- Keep at least {CASH_PERCENTAGE}% in USDC as safety buffer
- Only allocate to BUY recommendations
- Cash must be stored as USDC using USDC_ADDRESS: {USDC_ADDRESS}
"""

SWARM_TRADING_PROMPT = """You are an expert cryptocurrency trading AI analyzing market data.

CRITICAL RULES:
1. Your response MUST be EXACTLY one of these three words: Buy, Sell, or Do Nothing
2. Do NOT provide any explanation, reasoning, or additional text
3. Respond with ONLY the action word
4. Do NOT show your thinking process or internal reasoning

Analyze the market data below and decide:

- "Buy" = Strong bullish signals, recommend opening/holding position
- "Sell" = Bearish signals or major weakness, recommend closing position entirely
- "Do Nothing" = Unclear/neutral signals, recommend holding current state unchanged

IMPORTANT: "Do Nothing" means maintain current position (if we have one, keep it; if we don't, stay out)

RESPOND WITH ONLY ONE WORD: Buy, Sell, or Do Nothing"""

POSITION_ANALYSIS_PROMPT = """
You are an expert crypto trading analyst. Your task is to analyze the user's open positions based on the provided position summaries and current market data.

For EACH symbol, decide whether the user should **KEEP** the position open or **CLOSE** it. 
Explain briefly the reasoning behind each decision (e.g., "Trend weakening, RSI overbought").

⚠️ CRITICAL OUTPUT RULES:
- You MUST respond ONLY with a valid JSON object – no commentary, no Markdown, no code fences.
- JSON must be well-formed and parseable by Python's json.loads().
- The JSON must follow exactly this structure:

{
  "BTC": {
    "action": "KEEP",
    "reasoning": "Trend remains bullish; RSI under 60"
  },
  "ETH": {
    "action": "CLOSE",
    "reasoning": "Breakdown below MA40 with weak RSI"
  }
}

Do not include ```json or any other formatting around the JSON.
Respond ONLY with the raw JSON object.
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_account_balance(account=None):
    """Get account balance in USD based on exchange type"""
    try:
        if EXCHANGE in ["ASTER", "HYPERLIQUID"]:
            if EXCHANGE == "ASTER":
                balance_dict = n.get_account_balance()
                balance = balance_dict.get('available', 0) 
                cprint(f"💰 {EXCHANGE} Available Balance: ${balance:,.2f} USD", "cyan")
                
            else:  # HYPERLIQUID
                address = os.getenv("ACCOUNT_ADDRESS")
                if not address:
                    if account is None:
                        account = n._get_account_from_env()
                    address = account.address

                try:
                    if hasattr(n, 'get_available_balance'):
                        balance = n.get_available_balance(address)
                        cprint(f"💰 {EXCHANGE} Available (Free) USDC: ${balance}", "cyan")
                        
                        total_val = n.get_account_value(address)
                        cprint(f"   (Total Equity including positions: ${total_val})", "white")
                    else:
                        cprint("⚠️ Using Total Equity (Warning: Checks locked collateral)", "yellow")
                        balance = n.get_account_value(address)
                        
                except Exception as e:
                    cprint(f"❌ Error getting balance: {e}", "red")
                    balance = 0

            return float(balance)
            
        else:
            # SOLANA
            balance = n.get_token_balance_usd(USDC_ADDRESS)
            return balance
            
    except Exception as e:
        cprint(f"❌ Error getting account balance: {e}", "red")
        return 0


def calculate_position_size(account_balance):
    """Calculate position size based on account balance and MAX_POSITION_PERCENTAGE"""
    if EXCHANGE in ["ASTER", "HYPERLIQUID"]:
        margin_to_use = account_balance * (MAX_POSITION_PERCENTAGE / 100)
        notional_position = margin_to_use * LEVERAGE

        cprint(f"   📊 Position Calculation ({EXCHANGE}):", "yellow", attrs=['bold'])
        cprint(f"   💵 Account Balance: ${account_balance:,.2f}", "white")
        cprint(f"   📈 Max Position %: {MAX_POSITION_PERCENTAGE}%", "white")
        cprint(f"   💰 Margin to Use: ${margin_to_use:,.2f}", "green", attrs=['bold'])
        cprint(f"   ⚡ Leverage: {LEVERAGE}x", "white")
        cprint(f"   💎 Notional Position: ${notional_position:,.2f}", "cyan", attrs=['bold'])

        return notional_position
    else:
        # For Solana: No leverage, direct position size
        position_size = account_balance * (MAX_POSITION_PERCENTAGE / 100)

        cprint(f"   📊 Position Calculation (SOLANA):", "yellow", attrs=['bold'])
        cprint(f"   💵 USDC Balance: ${account_balance:,.2f}", "white")
        cprint(f"   📈 Max Position %: {MAX_POSITION_PERCENTAGE}%", "white")
        cprint(f"   💎 Position Size: ${position_size:,.2f}", "cyan", attrs=['bold'])

        return position_size

# ============================================================================
# TRADING AGENT CLASS
# ============================================================================

class TradingAgent:
    def __init__(self):
        # Initialize Account object with auto-cleaning for keys
        self.account = None
        if EXCHANGE == "HYPERLIQUID":
            cprint("🔑 Initializing Hyperliquid Account...", "cyan")
            try:
                raw_key = (
                   os.getenv("HYPER_LIQUID_KEY", "")
                   or os.getenv("HYPER_LIQUID_ETH_PRIVATE_KEY", "")
                )
                clean_key = raw_key.strip().replace('"', '').replace("'", "")
                self.account = Account.from_key(clean_key)

                self.address = os.getenv("ACCOUNT_ADDRESS")
                if not self.address:
                    self.address = self.account.address

                cprint(f"✅ Account loaded successfully! Address: {self.address}", "green")
            except Exception as e:
                cprint(f"❌ Error loading key: {e}", "red")
                sys.exit(1)

        # Check if using swarm mode or single model
        if USE_SWARM_MODE:
            cprint(
                f"\n🌊 Initializing Trading Agent in SWARM MODE (6 AI consensus)...",
                "cyan",
                attrs=["bold"]
            )
            self.swarm = SwarmAgent()
            cprint("✅ Swarm mode initialized with 6 AI models!", "green")

            cprint("💼 Initializing fast model for portfolio calculations...", "cyan")
            self.model = model_factory.get_model(AI_MODEL_TYPE, AI_MODEL_NAME)
            if self.model:
                cprint(f"✅ Allocation model ready: {self.model.model_name}", "green")
        else:
            cprint(f"\n🤖 Initializing Trading Agent with {AI_MODEL_TYPE} model...", "cyan")
            self.model = model_factory.get_model(AI_MODEL_TYPE, AI_MODEL_NAME)
            self.swarm = None

            if not self.model:
                cprint(f"❌ Failed to initialize {AI_MODEL_TYPE} model!", "red")
                cprint("Available models:", "yellow")
                for model_type in model_factory._models.keys():
                    cprint(f"   - {model_type}", "yellow")
                sys.exit(1)

            cprint(f"✅ Using model: {self.model.model_name}", "green")

        self.recommendations_df = pd.DataFrame(
            columns=["token", "action", "confidence", "reasoning"]
        )

        # Show which tokens will be analyzed
        cprint("\n🎯 Active Tokens for Trading:", "yellow", attrs=["bold"])
        if EXCHANGE in ["ASTER", "HYPERLIQUID"]:
            tokens_to_show = SYMBOLS
            cprint(f"🦈 Exchange: {EXCHANGE} (using symbols)", "cyan")
        else:
            tokens_to_show = MONITORED_TOKENS
            cprint(f"🦈 Exchange: SOLANA (using contract addresses)", "cyan")

        for i, token in enumerate(tokens_to_show, 1):
            token_display = token[:8] + "..." if len(token) > 8 else token
            cprint(f"   {i}. {token_display}", "cyan")

        cprint(
            f"\n⏱️  Estimated analysis time: ~{len(tokens_to_show) * 60} seconds\n",
            "yellow"
        )

        cprint(f"\n🦈 Active Exchange: {EXCHANGE}", "yellow", attrs=["bold"])
        cprint("📈 Trading Mode:", "yellow", attrs=["bold"])
        if LONG_ONLY:
            cprint("   📊 LONG ONLY - No shorting enabled", "cyan")
            cprint("   💡 SELL signals close positions, can't open shorts", "white")
        else:
            cprint("   ⚡ LONG/SHORT - Full directional trading", "green")
            cprint("   💡 SELL signals can close longs OR open shorts", "white")

        cprint("\n🤖 LLM Trading Agent initialized!", "green")
        log_and_print("\n🤖 LLM Trading Agent initialized!", "success")

    def chat_with_ai(self, system_prompt, user_content):
        """Send prompt to AI model via model factory"""
        try:
            response = self.model.generate_response(
                system_prompt=system_prompt,
                user_content=user_content,
                temperature=AI_TEMPERATURE,
                max_tokens=AI_MAX_TOKENS
            )

            if hasattr(response, "content"):
                return response.content
            return str(response)

        except Exception as e:
            cprint(f"❌ AI model error: {e}", "red")
            return None

    def _format_market_data_for_swarm(self, token, market_data):
        """Format market data into a clean, readable format for swarm analysis"""
        try:
            cprint(f"\n📊 MARKET DATA RECEIVED FOR {token[:8]}...", "cyan", attrs=["bold"])
            log_and_print(f"\n📊 MARKET DATA RECEIVED FOR {token[:8]}...", "info")

            if isinstance(market_data, pd.DataFrame):
                cprint(f"✅ DataFrame received: {len(market_data)} bars", "green")
                cprint(f"📅 Date range: {market_data.index[0]} to {market_data.index[-1]}", "yellow")
                cprint(f"🕐 Timeframe: {DATA_TIMEFRAME}", "yellow")

                cprint("\n📈 First 5 Bars (OHLCV):", "cyan")
                print(market_data.head().to_string())

                cprint("\n📉 Last 3 Bars (Most Recent):", "cyan")
                print(market_data.tail(3).to_string())

                formatted = f"""
TOKEN: {token}
TIMEFRAME: {DATA_TIMEFRAME} bars
TOTAL BARS: {len(market_data)}
DATE RANGE: {market_data.index[0]} to {market_data.index[-1]}

RECENT PRICE ACTION (Last 10 bars):
{market_data.tail(10).to_string()}

FULL DATASET:
{market_data.to_string()}
"""
            else:
                cprint(f"⚠️ Market data is not a DataFrame: {type(market_data)}", "yellow")
                formatted = f"TOKEN: {token}\nMARKET DATA:\n{str(market_data)}"

            if isinstance(market_data, dict) and "strategy_signals" in market_data:
                formatted += f"\n\nSTRATEGY SIGNALS:\n{json.dumps(market_data['strategy_signals'], indent=2)}"

            cprint("\n✅ Market data formatted and ready for analysis!\n", "green")
            return formatted

        except Exception as e:
            cprint(f"❌ Error formatting market data: {e}", "red")
            return str(market_data)

    def _calculate_swarm_consensus(self, swarm_result):
        """Calculate consensus from individual swarm responses"""
        try:
            votes = {"BUY": 0, "SELL": 0, "NOTHING": 0}
            model_votes = []

            for provider, data in swarm_result["responses"].items():
                if not data["success"]:
                    continue

                response_text = data["response"].strip().upper()

                if "BUY" in response_text:
                    votes["BUY"] += 1
                    model_votes.append(f"{provider}: Buy")
                elif "SELL" in response_text:
                    votes["SELL"] += 1
                    model_votes.append(f"{provider}: Sell")
                else:
                    votes["NOTHING"] += 1
                    model_votes.append(f"{provider}: Do Nothing")

            total_votes = sum(votes.values())
            if total_votes == 0:
                return "NOTHING", 0, "No valid responses from swarm"

            majority_action = max(votes, key=votes.get)
            majority_count = votes[majority_action]
            confidence = int((majority_count / total_votes) * 100)

            reasoning = f"Swarm Consensus ({total_votes} models voted):\n"
            reasoning += f"   Buy: {votes['BUY']} votes\n"
            reasoning += f"   Sell: {votes['SELL']} votes\n"
            reasoning += f"   Do Nothing: {votes['NOTHING']} votes\n\n"
            reasoning += "Individual votes:\n"
            reasoning += "\n".join(f"   - {vote}" for vote in model_votes)
            reasoning += f"\n\nMajority decision: {majority_action} ({confidence}% consensus)"

            cprint(
                f"\n🌊 Swarm Consensus: {majority_action} with {confidence}% agreement",
                "cyan",
                attrs=["bold"]
            )

            return majority_action, confidence, reasoning

        except Exception as e:
            cprint(f"❌ Error calculating swarm consensus: {e}", "red")
            return "NOTHING", 0, f"Error calculating consensus: {str(e)}"

    def fetch_all_open_positions(self):
        """Fetch all open positions across all symbols"""
        cprint("\n" + "=" * 60, "cyan")
        cprint("📊 FETCHING ALL OPEN POSITIONS", "white", "on_blue", attrs=["bold"])
        cprint("=" * 60, "cyan")

        all_positions = {}
        check_tokens = SYMBOLS if EXCHANGE in ["ASTER", "HYPERLIQUID"] else MONITORED_TOKENS

        for symbol in check_tokens:
            try:
                positions, im_in_pos, pos_size, pos_sym, entry_px, pnl_perc, is_long = n.get_position(
                    symbol, self.account
                )

                if im_in_pos and pos_size != 0:
                    position_data = {
                        "symbol": symbol,
                        "size": pos_size,
                        "entry_price": entry_px,
                        "pnl_percent": pnl_perc,
                        "is_long": is_long,
                        "side": "LONG 🟢" if is_long else "SHORT 🔴",
                        "age_hours": 0,
                    }

                    if symbol not in all_positions:
                        all_positions[symbol] = []
                    all_positions[symbol].append(position_data)

                    cprint(
                        f"   {symbol:<10} | {position_data['side']:<10} | "
                        f"Size: {pos_size:>10.4f} | Entry: ${entry_px:>10.2f} | "
                        f"PnL: {pnl_perc:>6.2f}%",
                        "cyan",
                    )

            except Exception as e:
                cprint(f"   ❌ Error fetching {symbol}: {e}", "red")
                continue

        if not all_positions:
            cprint("   ℹ️  No open positions found", "yellow")

        cprint("=" * 60 + "\n", "cyan")
        return all_positions

    def analyze_open_positions_with_ai(self, positions_data, market_data):
        """AI analyzes open positions and decides KEEP or CLOSE for each"""
        if not positions_data:
            return {}

        cprint("\n" + "=" * 60, "yellow")
        cprint("🤖 AI ANALYZING OPEN POSITIONS", "white", "on_magenta", attrs=["bold"])
        log_and_print("🤖 AI ANALYZING OPEN POSITIONS", "info")
        cprint("=" * 60, "yellow")

        # Build position summary
        position_summary = []
        for symbol, positions in positions_data.items():
            for pos in positions:
                position_summary.append({
                    "symbol": symbol,
                    "side": "LONG" if pos["is_long"] else "SHORT",
                    "size": pos["size"],
                    "entry_price": pos["entry_price"],
                    "current_pnl": pos["pnl_percent"],
                    "age_hours": pos["age_hours"],
                })

        # Format market conditions
        market_summary = {}
        for symbol in positions_data.keys():
            if symbol in market_data:
                df = market_data[symbol]
                if not df.empty:
                    latest = df.iloc[-1]

                    # Robustly detect the correct close column
                    if "Close" in df.columns:
                        current_price = latest["Close"]
                    elif "close" in df.columns:
                        current_price = latest["close"]
                    elif "close_price" in df.columns:
                        current_price = latest["close_price"]
                    elif "c" in df.columns:
                        current_price = latest["c"]
                    elif "price" in df.columns:
                        current_price = latest["price"]
                    else:
                        cprint(f"⚠️ No close price column found for {symbol}, skipping...", "yellow")
                        continue

                    market_summary[symbol] = {
                        "current_price": current_price,
                        "ma20": latest.get("MA20", 0),
                        "ma40": latest.get("MA40", 0),
                        "rsi": latest.get("RSI", 0),
                        "trend": "Bullish" if current_price > latest.get("MA20", 0) else "Bearish",
                    }

        user_prompt = f"""Analyze these open positions:

POSITIONS:
{json.dumps(position_summary, indent=2)}

CURRENT MARKET CONDITIONS:
{json.dumps(market_summary, indent=2)}

For each position, decide KEEP or CLOSE with reasoning.
Return ONLY valid JSON with the following structure:
{{
  "SYMBOL": {{
     "action": "KEEP" or "CLOSE",
     "reasoning": "short explanation"
  }}
}}"""

        try:
            response = self.chat_with_ai(POSITION_ANALYSIS_PROMPT, user_prompt)

            # --- Strip Markdown fences if model wrapped response in code blocks ---
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            # --- Try safe JSON extraction first ---
            decisions = extract_json_from_text(response)
            if not decisions:
                cprint("⚠️ AI response not valid JSON. Attempting text fallback...", "yellow")

                text = response.lower()
                decisions = {}
                for symbol in positions_data.keys():
                    if symbol.lower() in text:
                        if "close" in text or "sell" in text:
                            decisions[symbol] = {
                                "action": "CLOSE",
                                "reasoning": "Detected CLOSE or SELL keyword in fallback parsing.",
                            }
                        elif "keep" in text or "hold" in text or "open" in text:
                            decisions[symbol] = {
                                "action": "KEEP",
                                "reasoning": "Detected KEEP/HOLD keyword in fallback parsing.",
                            }
                        else:
                            decisions[symbol] = {
                                "action": "KEEP",
                                "reasoning": "No clear directive, default KEEP.",
                            }
                    else:
                        decisions[symbol] = {
                            "action": "KEEP",
                            "reasoning": "Symbol not mentioned, default KEEP.",
                        }

                cprint(f"🧠 Fallback interpreted decisions: {decisions}", "cyan")

            if not decisions:
                cprint("❌ Error: Could not interpret AI analysis at all.", "red")
                cprint(f"   Raw response: {response}", "yellow")
                return {}

            # --- Print parsed decisions cleanly ---
            cprint("\n🎯 AI POSITION DECISIONS:", "white", "on_magenta", attrs=["bold"])
            for symbol, decision in decisions.items():
                action = decision.get("action", "UNKNOWN")
                reason = decision.get("reasoning", "")
                color = "red" if action.upper() == "CLOSE" else "green"
                cprint(f"   {symbol:<10} → {action:<6} | {reason}", color)
                log_and_print(f"AI Decision → {symbol}: {action} | {reason}", "info")


            cprint("=" * 60 + "\n", "yellow")
            return decisions

        except Exception as e:
            cprint(f"❌ Error in AI analysis: {e}", "red")
            import traceback
            traceback.print_exc()
            return {}

    def execute_position_closes(self, close_decisions):
        """Execute closes for positions marked by AI"""
        if not close_decisions:
            return

        cprint("\n" + "=" * 60, "red")
        cprint("🔄 EXECUTING POSITION CLOSES", "white", "on_red", attrs=["bold"])
        cprint("=" * 60, "red")

        closed_count = 0

        for symbol, decision in close_decisions.items():
            if decision["action"] == "CLOSE":
                try:
                    cprint(f"\n   📉 Closing {symbol}...", "yellow")
                    cprint(f"   💡 Reason: {decision['reasoning']}", "white")

                    n.close_complete_position(symbol, self.account)

                    cprint(f"✅ {symbol} position closed successfully", "green", attrs=["bold"])
                    log_and_print(f"✅ Closed {symbol} | Reason: {decision['reasoning']}", "success")
                   
                    closed_count += 1
                    time.sleep(2)

                except Exception as e:
                    cprint(f"   ❌ Error closing {symbol}: {e}", "red")
                    import traceback
                    traceback.print_exc()

        if closed_count > 0:
            cprint(
                f"\n✨ Successfully closed {closed_count} position(s)",
                "white",
                "on_green",
                attrs=["bold"],
            )
        else:
            cprint("\n   ℹ️  No positions needed closing", "cyan")

        cprint("=" * 60 + "\n", "red")

    def analyze_market_data(self, token, market_data):
        """Analyze market data using AI model (single or swarm mode)"""
        try:
            if token in EXCLUDED_TOKENS:
                print(f"⚠️ Skipping analysis for excluded token: {token}")
                return None

            # Fetch current position context
            position_context = "CURRENT POSITION: None (You have no exposure)."

            try:
                raw_pos_data = n.get_position(token, self.account)
                _, im_in_pos, pos_size, _, entry_px, pnl_perc, is_long = raw_pos_data

                if im_in_pos:
                    side = "LONG" if is_long else "SHORT"

                    if entry_px == 0 and pnl_perc == 0:
                        position_context = (
                            f"CURRENT POSITION: ✅ Active {side} (Spot) | Size: {pos_size}"
                        )
                    else:
                        position_context = (
                            f"CURRENT POSITION: ✅ Active {side} | "
                            f"Size: {pos_size} | Entry: ${entry_px:.4f} | "
                            f"PnL: {pnl_perc:.2f}%"
                        )
            except Exception as e:
                cprint(f"⚠️ Error fetching position context: {e}", "yellow")

            cprint(f"   ℹ️  Context: {position_context}", "cyan")

            # SWARM MODE
            if USE_SWARM_MODE:
                cprint(
                    f"\n🌊 Analyzing {token[:8]}... with SWARM (6 AI models voting)",
                    "cyan",
                    attrs=["bold"],
                )

                base_market_data = self._format_market_data_for_swarm(token, market_data)
                formatted_data = f"{position_context}\n\n{base_market_data}"

                swarm_result = self.swarm.query(
                    prompt=formatted_data, system_prompt=SWARM_TRADING_PROMPT
                )

                if not swarm_result:
                    cprint(f"❌ No response from swarm for {token}", "red")
                    return None

                action, confidence, reasoning = self._calculate_swarm_consensus(
                    swarm_result
                )

                self.recommendations_df = pd.concat(
                    [
                        self.recommendations_df,
                        pd.DataFrame(
                            [
                                {
                                    "token": token,
                                    "action": action,
                                    "confidence": confidence,
                                    "reasoning": reasoning,
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )

                cprint(f"✅ Swarm analysis complete for {token[:8]}!", "green")
                return swarm_result

            # SINGLE MODEL MODE
            else:
                if "strategy_signals" in market_data:
                    strategy_context = (
                        f"Strategy Signals Available:\n"
                        f"{json.dumps(market_data['strategy_signals'], indent=2)}"
                    )
                else:
                    strategy_context = "No strategy signals available."

                response = self.chat_with_ai(
                    TRADING_PROMPT.format(
                        strategy_context=strategy_context,
                        position_context=position_context,
                    ),
                    f"Market Data to Analyze:\n{market_data}",
                )

                if not response:
                    cprint(f"❌ No response from AI for {token}", "red")
                    return None

                lines = response.split("\n")
                action = lines[0].strip() if lines else "NOTHING"

                confidence = 0
                for line in lines:
                    if "confidence" in line.lower():
                        try:
                            confidence = int("".join(filter(str.isdigit, line)))
                        except Exception:
                            confidence = 50

                reasoning = (
                    "\n".join(lines[1:]) if len(lines) > 1 else "No detailed reasoning provided"
                )

                self.recommendations_df = pd.concat(
                    [
                        self.recommendations_df,
                        pd.DataFrame(
                            [
                                {
                                    "token": token,
                                    "action": action,
                                    "confidence": confidence,
                                    "reasoning": reasoning,
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )

                log_and_print(f"🎯 AI Analysis Complete for {token[:4]}!", "success")
                log_and_print(f"Reasoning for {token[:4]}:\n{reasoning}", "info")

                return response

        except Exception as e:
            print(f"❌ Error in AI analysis: {str(e)}")
            self.recommendations_df = pd.concat(
                [
                    self.recommendations_df,
                    pd.DataFrame(
                        [
                            {
                                "token": token,
                                "action": "NOTHING",
                                "confidence": 0,
                                "reasoning": f"Error during analysis: {str(e)}",
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )
            return None

    def allocate_portfolio(self):
        """Get AI-recommended portfolio allocation"""
        try:
            cprint("\n💰 Calculating optimal portfolio allocation...", "cyan")

            # Filter only BUY recommendations
            buy_recommendations = self.recommendations_df[
                self.recommendations_df["action"] == "BUY"
            ]

            if buy_recommendations.empty:
                cprint("✅ No BUY recommendations. Skipping allocation.", "green")
                return {}

            # Get account balance (equity)
            account_balance = get_account_balance(self.account)
            if account_balance <= 0:
                cprint("❌ Account balance is zero. Cannot allocate.", "red")
                return None

            # Calculate position sizing
            max_position_size = account_balance * (MAX_POSITION_PERCENTAGE / 100)

            cprint(
                f"🎯 Maximum position size: ${max_position_size:.2f} "
                f"({MAX_POSITION_PERCENTAGE}% of ${account_balance:.2f})",
                "cyan",
            )

            # Token set depends on exchange type
            if EXCHANGE in ["ASTER", "HYPERLIQUID"]:
                available_tokens = SYMBOLS
            else:
                available_tokens = MONITORED_TOKENS

            # --- AI prompt for allocation ---
            allocation_prompt = f"""You are our Portfolio Allocation AI 🌙

Given:
- Total portfolio size: ${account_balance}
- Maximum position size: ${max_position_size} ({MAX_POSITION_PERCENTAGE}% of total)
- Minimum cash (USDC) buffer: {CASH_PERCENTAGE}%
- Available tokens: {available_tokens}
- USDC Address: {USDC_ADDRESS}

Provide a portfolio allocation that:
1. Never exceeds max position size per token
2. Maintains minimum cash buffer
3. Returns allocation as a JSON object with token addresses as keys and USD amounts as values
4. Uses exact USDC address: {USDC_ADDRESS} for cash allocation

Example format:
{{
    "token_address": amount_in_usd,
    "{USDC_ADDRESS}": remaining_cash_amount
}}"""

            # --- Compose user context ---
            user_content = f"""
Total Portfolio Size: ${account_balance:,.2f} USD
Trading Recommendations (BUY signals only):
{buy_recommendations.to_string()}
"""

            # --- Call AI model ---
            response = self.chat_with_ai(allocation_prompt, user_content)

            if not response:
                cprint("❌ No response from AI for portfolio allocation", "red")
                return None

            # --- Safely parse JSON ---
            allocations = extract_json_from_text(response)
            if not allocations:
                cprint("❌ Error parsing allocation JSON: No JSON object found in the response", "red")
                cprint(f"   Raw response: {response}", "yellow")
                return None

            # --- Normalize keys if AI returned string literal 'USDC_ADDRESS' ---
            if "USDC_ADDRESS" in allocations and USDC_ADDRESS not in allocations:
                amount = allocations.pop("USDC_ADDRESS")
                allocations[USDC_ADDRESS] = amount

            # --- Validate and normalize allocations ---
            valid_allocations = {k: float(v) for k, v in allocations.items()
                                if isinstance(v, (int, float, str)) and str(v).replace('.', '', 1).isdigit()}
            total_margin = sum(valid_allocations.values())
            target_margin = account_balance * (MAX_POSITION_PERCENTAGE / 100)
        
            # --- Scale allocations to use 90% of equity ---
            if total_margin > 0:
                scale_factor = target_margin / total_margin
                for k in valid_allocations.keys():
                    valid_allocations[k] = round(valid_allocations[k] * scale_factor, 2)
        
            # --- Enforce minimum trade size (≥ $12 notional) ---
            min_margin = 12 / LEVERAGE
            adjusted = False
            for k, v in valid_allocations.items():
                if k == USDC_ADDRESS:
                    continue  # skip cash buffer
                if v < min_margin:
                    cprint(f"⚠️ Raising {k} from ${v:.2f} to minimum ${min_margin:.2f}", "yellow")
                    valid_allocations[k] = round(min_margin, 2)
                    adjusted = True
        
            # --- Rebalance if any raises occurred ---
            if adjusted:
                total_margin = sum(v for k, v in valid_allocations.items() if k != USDC_ADDRESS)
                scale_factor = target_margin / total_margin
                for k in valid_allocations.keys():
                    if k != USDC_ADDRESS:
                        valid_allocations[k] = round(valid_allocations[k] * scale_factor, 2)
        
            allocations = valid_allocations

            # --- Pretty print allocation ---
            cprint("\n📊 AI Portfolio Allocation:", "green", attrs=["bold"])
            for token, amount in allocations.items():
                token_display = "USDC (Cash)" if token == USDC_ADDRESS else token
                try:
                    cprint(f"   • {token_display}: ${float(amount):,.2f}", "green")
                except (ValueError, TypeError):
                    cprint(f"   • {token_display}: {amount} (Invalid Amount)", "red")

            return allocations

        except Exception as e:
            cprint(f"❌ Error in portfolio allocation: {str(e)}", "red")
            import traceback
            traceback.print_exc()
            return None

    def execute_allocations(self, allocation_dict):
        """Execute the allocations using AI entry for each position"""
        try:
            print("\n🚀 Moon Dev executing portfolio allocations...")

            for token, amount in allocation_dict.items():
                if token in EXCLUDED_TOKENS:
                    print(f"💵 Keeping ${float(amount):.2f} in {token}")
                    continue

                print(f"\n🎯 Processing allocation for {token}...")

                try:
                    if EXCHANGE == "HYPERLIQUID":
                        current_position = n.get_token_balance_usd(token, self.account)
                    else:
                        current_position = n.get_token_balance_usd(token)

                    target_allocation = amount

                    print(f"🎯 Target allocation: ${target_allocation:.2f} USD")
                    print(f"📊 Current position: ${current_position:.2f} USD")
                    effective_value = float(target_allocation) * LEVERAGE
                    print(f"⚡ Trade exposure (with {LEVERAGE}x): ${effective_value:.2f}")

                    if current_position < target_allocation:
                        print(f"✨ Executing entry for {token}")

                        if EXCHANGE == "HYPERLIQUID":
                            n.ai_entry(token, amount, leverage=LEVERAGE, account=self.account)
                        elif EXCHANGE == "ASTER":
                            n.ai_entry(token, amount, leverage=LEVERAGE)
                        else:
                            n.ai_entry(token, amount)

                        print(f"✅ Entry complete for {token}")
                        log_and_print(f"🚀 Opened new {token} position for ${amount:.2f}", "success")

                    
                        # Log position open
                        try:
                            import sys
                            from pathlib import Path
                            parent_dir = Path(__file__).parent.parent
                            if str(parent_dir) not in sys.path:
                                sys.path.insert(0, str(parent_dir))
                            from trading_app import log_position_open
                            
                            # Determine position value (with leverage)
                            notional_value = float(amount) * LEVERAGE
                            log_position_open(token, "LONG", notional_value)
                        except Exception:
                            pass
                    else:
                        print(f"⏸️ Position already at target size for {token}")

                except Exception as e:
                    print(f"❌ Error executing entry for {token}: {str(e)}")

                time.sleep(2)

        except Exception as e:
            print(f"❌ Error executing allocations: {str(e)}")
            print("🔧 Moon Dev suggests checking the logs and trying again!")

    def handle_exits(self):
        """Check and exit positions based on SELL recommendations"""
        import inspect

        cprint("\n🔄 Checking for positions to exit...", "white", "on_blue")

        for _, row in self.recommendations_df.iterrows():
            token = row["token"]
            token_short = token[:8] + "..." if len(token) > 8 else token

            if token in EXCLUDED_TOKENS:
                continue

            action = row["action"]

            if EXCHANGE == "HYPERLIQUID":
                current_position = n.get_token_balance_usd(token, self.account)
            else:
                current_position = n.get_token_balance_usd(token)

            cprint(f"\n{'=' * 60}", "cyan")
            cprint(f"🎯 Token: {token_short}", "cyan", attrs=["bold"])
            cprint(f"🤖 Signal: {action} ({row['confidence']}% confidence)", "yellow", attrs=["bold"])
            cprint(f"💼 Current Position: ${current_position:.2f}", "white")
            cprint(f"{'=' * 60}", "cyan")

            if current_position > 0:
                # ============= CASE: HAVE POSITION =============
                if action == "SELL":
                    cprint("🚨 SELL signal with position - CLOSING POSITION", "white", "on_red")
                    try:
                        if EXCHANGE == "HYPERLIQUID":
                            n.close_complete_position(token, self.account)
                        else:
                            n.chunk_kill(token, max_usd_order_size, slippage)
                        cprint("✅ Position closed successfully!", "white", "on_green")
                        log_and_print(f"Closed {token} position due to signal", "warning")

                    except Exception as e:
                        cprint(f"❌ Error closing position: {str(e)}", "white", "on_red")

                elif action == "NOTHING":
                    cprint("⏸️  DO NOTHING signal - HOLDING POSITION", "white", "on_blue")
                    cprint(f"💎 Maintaining ${current_position:.2f} position", "cyan")

                else:
                    cprint("✅ BUY signal - KEEPING POSITION", "white", "on_green")
                    cprint(f"💎 Maintaining ${current_position:.2f} position", "cyan")

            else:
                # ============= CASE: NO POSITION =============
                if action == "SELL":
                    if LONG_ONLY:
                        cprint("⏭️  SELL signal but NO POSITION to close", "white", "on_blue")
                        cprint("📊 LONG ONLY mode: Can't open short, doing nothing", "cyan")
                    else:
                        account_balance = get_account_balance(self.account)
                        position_size = calculate_position_size(account_balance)

                        cprint("📉 SELL signal with no position - OPENING SHORT", "white", "on_red")
                        cprint(f"⚡ {EXCHANGE} mode: Opening ${position_size:,.2f} short position", "yellow")

                        try:
                            # Dynamically detect which function to use
                            if hasattr(n, "open_short"):
                                fn = n.open_short
                                cprint(f"📉 Executing open_short (${position_size:,.2f})...", "yellow")
                            else:
                                fn = n.market_sell
                                cprint(f"📉 Executing market_sell (${position_size:,.2f})...", "yellow")

                            # Build kwargs dynamically depending on function signature
                            params = inspect.signature(fn).parameters
                            kwargs = {}
                            if "leverage" in params:
                                kwargs["leverage"] = LEVERAGE
                            if "account" in params:
                                kwargs["account"] = self.account
                            if "slippage" in params:
                                kwargs["slippage"] = slippage

                            # Safe function call
                            fn(token, position_size, **kwargs)

                            cprint("✅ Short position opened successfully!", "white", "on_green")
                            log_and_print(f"📉 Opened new {token} SHORT position", "success")

                            
                            # Log short position open
                            try:
                                import sys
                                from pathlib import Path
                                parent_dir = Path(__file__).parent.parent
                                if str(parent_dir) not in sys.path:
                                    sys.path.insert(0, str(parent_dir))
                                from trading_app import log_position_open
                                
                                log_position_open(token, "SHORT", position_size)
                            except Exception:
                                pass

                        except Exception as e:
                            cprint(f"❌ Error opening short position: {str(e)}", "white", "on_red")

                elif action == "NOTHING":
                    cprint("⏸️  DO NOTHING signal with no position", "white", "on_blue")
                    cprint("⏭️  Staying out of market", "cyan")

                else:
                    # BUY signal with no position
                    cprint("📈 BUY signal with no position", "white", "on_green")

                    if USE_PORTFOLIO_ALLOCATION:
                        cprint("📊 Portfolio allocation will handle entry", "white", "on_cyan")
                    else:
                        account_balance = get_account_balance(self.account)
                        position_size = calculate_position_size(account_balance)

                        cprint("💰 Opening position at MAX_POSITION_PERCENTAGE", "white", "on_green")

                        try:
                            if EXCHANGE in ["ASTER", "HYPERLIQUID"]:
                                if EXCHANGE == "HYPERLIQUID":
                                    success = n.ai_entry(token, position_size, leverage=LEVERAGE, account=self.account)
                                else:
                                    success = n.ai_entry(token, position_size, leverage=LEVERAGE)
                            else:
                                success = n.ai_entry(token, position_size)

                            if success:
                                cprint("✅ LONG Position opened successfully!", "white", "on_green")
                                log_and_print(f"📈 Opened new {token} LONG position", "success")

                                
                                time.sleep(2)

                                # Verify position
                                try:
                                    if EXCHANGE == "HYPERLIQUID":
                                        raw_pos_data = n.get_position(token, self.account)
                                    else:
                                        raw_pos_data = n.get_position(token)

                                    _, im_in_pos, pos_size, _, _, _, _ = raw_pos_data

                                    if im_in_pos and pos_size != 0:
                                        cprint(f"📊 Confirmed: Position Active (Size: {pos_size})", "green", attrs=["bold"])
                                        
                                        # Log position open
                                        try:
                                            import sys
                                            from pathlib import Path
                                            parent_dir = Path(__file__).parent.parent
                                            if str(parent_dir) not in sys.path:
                                                sys.path.insert(0, str(parent_dir))
                                            from trading_app import log_position_open
                                            
                                            notional_value = float(position_size) * LEVERAGE
                                            log_position_open(token, "LONG", notional_value)
                                        except Exception:
                                            pass
                                    else:
                                        cprint("⚠️  Warning: Position verification failed - no position found!", "yellow")

                                except Exception as e:
                                    cprint(f"⚠️  Verification check error: {e}", "yellow")

                            else:
                                cprint("❌ Position not opened (check errors above)", "white", "on_red")
                                
                        except Exception as e:
                            cprint(f"❌ Error opening position: {str(e)}", "white", "on_red")

    def show_final_portfolio_report(self):
        """Display final portfolio status - NO LOOPS, just a snapshot"""
        cprint("\n" + "=" * 60, "cyan")
        cprint("📊 FINAL PORTFOLIO REPORT", "white", "on_blue", attrs=["bold"])
        cprint("=" * 60, "cyan")

        check_tokens = SYMBOLS if EXCHANGE in ["ASTER", "HYPERLIQUID"] else MONITORED_TOKENS
        active_positions = []

        # Print header
        print(f"   {'TOKEN':<10} | {'SIDE':<10} | {'SIZE':<12} | {'ENTRY':<12} | {'PNL %':<10}")
        print("   " + "-" * 65)

        for token in check_tokens:
            try:
                pos_data = n.get_position(token, self.account)
                _, im_in_pos, pos_size, _, entry_px, pnl_perc, is_long = pos_data

                if im_in_pos and pos_size != 0:
                    side_icon = "LONG 🟢" if is_long else "SHORT 🔴"
                    entry_str = f"${entry_px:.2f}" if entry_px != 0 else "-"
                    pnl_str = f"{pnl_perc:+.2f}%" if pnl_perc != 0 else "-"

                    print(
                        f"   {token:<10} | {side_icon:<10} | {pos_size:<12.4f} | "
                        f"{entry_str:<12} | {pnl_str:<10}"
                    )
                    active_positions.append(token)

            except Exception:
                pass  # Silently skip errors to keep report clean

        if not active_positions:
            cprint("   (No active positions)", "cyan")

        cprint("=" * 60 + "\n", "cyan")

    def run(self):
        """Run the trading agent (implements BaseAgent interface)"""
        self.run_trading_cycle()

    def run_trading_cycle(self, strategy_signals=None):
        """Enhanced trading cycle with position management"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cprint(f"\n{'=' * 80}", "cyan")
            cprint(f"🔄 TRADING CYCLE START: {current_time}", "white", "on_green", attrs=["bold"])
            cprint(f"{'=' * 80}", "cyan")

            # STEP 1: FETCH ALL OPEN POSITIONS
            open_positions = self.fetch_all_open_positions()

            # STEP 2: COLLECT MARKET DATA
            if EXCHANGE in ["ASTER", "HYPERLIQUID"]:
                tokens_to_trade = SYMBOLS
            else:
                tokens_to_trade = MONITORED_TOKENS

            cprint("📊 Collecting market data for analysis...", "white", "on_blue")
            market_data = collect_all_tokens(
                tokens=tokens_to_trade,
                days_back=DAYSBACK_4_DATA,
                timeframe=DATA_TIMEFRAME,
                exchange=EXCHANGE,
            )

            # STEP 3: AI ANALYZES OPEN POSITIONS
            close_decisions = {}
            if open_positions:
                close_decisions = self.analyze_open_positions_with_ai(open_positions, market_data)
                self.execute_position_closes(close_decisions)

            # STEP 4: REFETCH POSITIONS & MARKET DATA AFTER CLOSURES
            time.sleep(2)  # short delay to allow exchange updates
            open_positions = self.fetch_all_open_positions()
            cprint("📊 Refreshing market data after position updates...", "white", "on_blue")
            market_data = collect_all_tokens(
                tokens=tokens_to_trade,
                days_back=DAYSBACK_4_DATA,
                timeframe=DATA_TIMEFRAME,
                exchange=EXCHANGE,
            )

            # STEP 5: ANALYZE TOKENS FOR NEW ENTRIES
            cprint("\n📈 Analyzing tokens for new entry opportunities...", "white", "on_blue")
            for token, data in market_data.items():
                cprint(f"\n🤖 Analyzing {token}...", "white", "on_green")
                log_and_print(f"\n🤖 Analyzing {token}...", "info")


                if strategy_signals and token in strategy_signals:
                    data["strategy_signals"] = strategy_signals[token]

                analysis = self.analyze_market_data(token, data)
                if analysis:
                    print(f"\n📈 Analysis for {token}:")
                    print(analysis)
                    print("\n" + "=" * 50 + "\n")

            # STEP 6: SHOW RECOMMENDATIONS
            cprint("\n📊 AI TRADING RECOMMENDATIONS:", "white", "on_blue")
            summary_df = self.recommendations_df[["token", "action", "confidence"]].copy()
            print(summary_df.to_string(index=False))

            # STEP 7: HANDLE EXITS & ENTRIES
            self.handle_exits()
            buy_recommendations = self.recommendations_df[self.recommendations_df["action"] == "BUY"]

            if USE_PORTFOLIO_ALLOCATION and len(buy_recommendations) > 0:
                allocation = self.allocate_portfolio()
                if allocation:
                    cprint("\n💼 Executing portfolio allocations...", "white", "on_blue")
                    log_and_print("\n💼 Executing portfolio allocations...", "info")
                    self.execute_allocations(allocation)

            # STEP 8: FINAL PORTFOLIO REPORT
            self.show_final_portfolio_report()

            # Clean up temp data
            try:
                if os.path.exists("temp_data"):
                    for file in os.listdir("temp_data"):
                        if file.endswith("_latest.csv"):
                            os.remove(os.path.join("temp_data", file))
            except Exception as e:
                cprint(f"⚠️ Error cleaning temp data: {e}", "yellow")

            cprint(f"\n{'=' * 80}", "cyan")
            cprint("✅ TRADING CYCLE COMPLETE", "white", "on_green", attrs=["bold"])
            log_and_print("Trading cycle complete", "success")
            cprint(f"{'=' * 80}\n", "cyan")

            # --- Display Account Balance and Invested Totals ---
            try:
                account_balance = get_account_balance(self.account)
            except Exception as e:
                cprint(f"⚠️ Could not retrieve account balance: {e}", "yellow")
                account_balance = 0.0

            try:
                invested_total = 0.0
                positions = self.fetch_all_open_positions()
                for symbol, pos_list in positions.items():
                    for p in pos_list:
                        size = abs(float(p.get("size", 0)))
                        entry_price = float(p.get("entry_price", 0))
                        invested_total += size * entry_price
            except Exception as e:
                cprint(f"⚠️ Could not calculate invested total: {e}", "yellow")
                invested_total = 0.0

            cprint(f"💰 Account Balance: ${account_balance:,.2f}", "cyan", attrs=["bold"])
            cprint(f"🚀 Invested Total: ${invested_total:,.2f}", "cyan", attrs=["bold"])

        except Exception as e:
            cprint(f"\n❌ Error in trading cycle: {e}", "white", "on_red")
            import traceback
            traceback.print_exc()


def main():
    """Main function - simple cycle every X minutes"""
    cprint("🚀 AI Trading System Starting Up! 🚀", "white", "on_blue")
    print("🛑 Press Ctrl+C to stop.\n")
    
    agent = TradingAgent()
    
    while True:
        try:
            # Run the complete cycle
            agent.run_trading_cycle()
            
            # Sleep until next cycle
            next_run = datetime.now() + timedelta(minutes=SLEEP_BETWEEN_RUNS_MINUTES)
            cprint(f"\n⏰ Next cycle at UTC: {next_run.strftime('%d-%m-%Y %H:%M:%S')}", "white", "on_green")
            time.sleep(SLEEP_BETWEEN_RUNS_MINUTES * 60)
            log_and_print(f"\n⏰ Next cycle in {timedelta(minutes=SLEEP_BETWEEN_RUNS_MINUTES)} minutes"}, "info")
            
        except KeyboardInterrupt:
            cprint("\n👋 AI Agent shutting down gracefully...", "white", "on_blue")
            log_and_print("\n👋 AI Agent shutting down gracefully...", "info")
            break
        except Exception as e:
            cprint(f"\n❌ Error in main loop: {e}", "white", "on_red")
            import traceback
            traceback.print_exc()
            time.sleep(SLEEP_BETWEEN_RUNS_MINUTES * 60)


if __name__ == "__main__":
    main()
