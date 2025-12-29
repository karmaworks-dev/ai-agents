#!/usr/bin/env python3
"""
Trading Dashboard Backend
=======
Trading Dashboard Backend
Production-ready Flask app for HyperLiquid trading
"""
import os
import sys
import json
import time
import threading
from threading import Lock  # ADD THIS LINE
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from flask_cors import CORS
import signal  # ADD THIS
import atexit  # ADD THIS

# ============================================================================
# SETUP & CONFIGURATION
# ============================================================================

# Add project root to Python path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables
load_dotenv()

# Initialize Flask with correct paths
DASHBOARD_DIR = BASE_DIR / "dashboard"
app = Flask(__name__,
    template_folder=str(DASHBOARD_DIR / "templates"),
    static_folder=str(DASHBOARD_DIR / "static"),
    static_url_path='/static'
)

# Enable CORS
CORS(app)

# Data storage directories
DATA_DIR = BASE_DIR / "src" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRADES_FILE = DATA_DIR / "trades.json"
HISTORY_FILE = DATA_DIR / "balance_history.json"
CONSOLE_FILE = DATA_DIR / "console_logs.json"
AGENT_STATE_FILE = DATA_DIR / "agent_state.json"

# Agent control variables

agent_thread = None
agent_running = False  # Always start stopped - never auto-start
stop_agent_flag = False
shutdown_in_progress = False  # Shutdown Flag
agent_executing = False  # Agent Trade Cycle Active Flag - True when actively analyzing, False when waiting

agent_lock = Lock()  # Protects all agent control flags

# Symbols list (for trading agent reference)
SYMBOLS = [
    'ETH',        # Ethereum
    'BTC',        # Bitcoin
    'SOL',        # Solana
    'AAVE',       # Aave
    'LINK',       # Chainlink
    'LTC',        # Litecoin
    'FARTCOIN',   # FartCoin
]

# Exchange type
EXCHANGE = "HYPERLIQUID"

# ============================================================================
# IMPORT TRADING FUNCTIONS (with fallback)
# ============================================================================
EXCHANGE_CONNECTED = False
try:
    # Try importing from nice_funcs.py (local file)
    import nice_funcs_hyperliquid as n
    from eth_account import Account
    
    def _get_account():
        """Get HyperLiquid account from environment (reads HYPER_LIQUID_ETH_PRIVATE_KEY)"""
        key = os.getenv("HYPER_LIQUID_ETH_PRIVATE_KEY", "") or os.getenv("HYPERLIQUID_KEY", "")
        key = (key or "").strip().replace('"', '').replace("'", "")
        if not key:
            raise RuntimeError("Missing HYPER_LIQUID_ETH_PRIVATE_KEY (private key) in environment.")
        if key.startswith("0x"):
            key = key[2:]
        if len(key) != 64:
            raise RuntimeError("HYPER_LIQUID_ETH_PRIVATE_KEY must be 64 hex chars (32 bytes) after removing 0x.")
        return Account.from_key(key)
    
    EXCHANGE_CONNECTED = True
    print("✅ HyperLiquid functions loaded from nice_funcs.py")
    
except ImportError:
    try:
        # Fallback: Try importing from src module
        from src import nice_funcs_hyperliquid as n
        from eth_account import Account
        
        def _get_account():
            key = os.getenv("HYPER_LIQUID_ETH_PRIVATE_KEY", "") or os.getenv("HYPERLIQUID_KEY", "")
            key = (key or "").strip().replace('"', '').replace("'", "")
            if not key:
                raise RuntimeError("Missing HYPER_LIQUID_ETH_PRIVATE_KEY (private key) in environment.")
            if key.startswith("0x"):
                key = key[2:]
            if len(key) != 64:
                raise RuntimeError("HYPER_LIQUID_ETH_PRIVATE_KEY must be 64 hex chars (32 bytes) after removing 0x.")
            return Account.from_key(key)
        
        EXCHANGE_CONNECTED = True
        print("✅ HyperLiquid functions loaded from src.nice_funcs_hyperliquid")
        
    except ImportError as e:
        print(f"⚠️ Warning: Could not import HyperLiquid functions: {e}")
        print("⚠️ Dashboard will run in DEMO mode with simulated data")
        
        # Create dummy functions for demo mode
        class DummyAccount:
            address = "0x0000000000000000000000000000000000000000"
        
        def _get_account():
            return DummyAccount()
        
        n = None


# ============================================================================
# DATA COLLECTION FUNCTIONS
# ============================================================================

def get_account_data():
    """Fetch live account data from HyperLiquid"""
    if not EXCHANGE_CONNECTED or n is None:
        # Demo mode data
        return {
            "account_balance": 10.0,
            "total_equity": 10.0,
            "pnl": 0.0,
            "status": "Demo Mode",
            "exchange": "HyperLiquid (Disconnected)",
            "agent_running": agent_running
        }
    
    try:
        account = _get_account()
        address = os.getenv("ACCOUNT_ADDRESS", account.address)
        
        # Get live data using the correct function names
        if hasattr(n, 'get_available_balance'):
            available_balance = float(n.get_available_balance(address))
        else:
            available_balance = 10.0
        
        if hasattr(n, 'get_account_value'):
            total_equity = float(n.get_account_value(address))
        else:
            total_equity = 10.0
        
        # Calculate PnL (starting balance from config or default $10)
        starting_balance = 10.0
        pnl = total_equity - starting_balance
        
        # Save to history
        save_balance_history(total_equity)
        
        return {
            "account_balance": round(available_balance, 2),
            "total_equity": round(total_equity, 2),
            "pnl": round(pnl, 2),
            "status": "Running" if agent_running else "Connected",
            "exchange": "HyperLiquid",
            "agent_running": agent_running
        }
        
    except Exception as e:
        error_msg = f"Error fetching account data: {str(e)}"
        print(f"❌ {error_msg}")
        add_console_log(f"❌ {error_msg}")
        
        return {
            "account_balance": 0.0,
            "total_equity": 0.0,
            "pnl": 0.0,
            "status": "Error",
            "exchange": "HyperLiquid",
            "agent_running": agent_running
        }


def get_positions_data():
    """Fetch ALL live open positions from HyperLiquid"""
    if not EXCHANGE_CONNECTED or n is None:
        print("⚠️ Exchange not connected or nice_funcs not loaded")
        return []

    try:
        # Get account
        account = _get_account()
        address = os.getenv("ACCOUNT_ADDRESS", account.address)
        
        print(f"\n{'='*60}")
        print(f"🔍 Fetching positions for address: {address}")
        print(f"{'='*60}")
        
        # Import HyperLiquid SDK
        from hyperliquid.info import Info
        from hyperliquid.utils import constants
        
        # Connect to HyperLiquid Info API
        info = Info(constants.MAINNET_API_URL, skip_ws=True)
        user_state = info.user_state(address)
        
        positions = []
        
        # Check if assetPositions exists
        if "assetPositions" not in user_state:
            print("❌ No 'assetPositions' field in user_state")
            print(f"Available fields: {list(user_state.keys())}")
            return []
        
        asset_positions = user_state["assetPositions"]
        print(f"📊 Found {len(asset_positions)} asset position entries")
        
        # Loop through ALL asset positions
        for idx, position in enumerate(asset_positions):
            try:
                raw_pos = position.get("position", {})
                symbol = raw_pos.get("coin", "Unknown")
                pos_size = float(raw_pos.get("szi", 0))
                
                print(f"\n   Position {idx + 1}: {symbol} | Size: {pos_size}")
                
                # Only include non-zero positions
                if pos_size == 0:
                    print(f"   ⏭️  Skipping {symbol} (size = 0)")
                    continue
                
                # Get position details
                entry_px = float(raw_pos.get("entryPx", 0))
                pnl_perc = float(raw_pos.get("returnOnEquity", 0)) * 100
                is_long = pos_size > 0
                side = "LONG" if is_long else "SHORT"
                
                print(f"   📍 {symbol} {side} position detected!")
                print(f"      Entry: ${entry_px:.2f} | PnL: {pnl_perc:.2f}%")
                
                # Fetch current mark price
                try:
                    ask, bid, _ = n.ask_bid(symbol)
                    mark_price = (ask + bid) / 2
                    print(f"      Mark price: ${mark_price:.2f}")
                except Exception as price_err:
                    print(f"      ⚠️ Could not fetch mark price: {price_err}")
                    mark_price = entry_px
                    print(f"      Using entry price as fallback: ${mark_price:.2f}")
                
                # Calculate position value in USD
                position_value = abs(pos_size) * mark_price
                
                print(f"      Position value: ${position_value:.2f}")
                
                # Add to positions array
                position_obj = {
                    "symbol": symbol,
                    "size": float(pos_size),
                    "entry_price": float(entry_px),
                    "mark_price": float(mark_price),
                    "position_value": float(position_value),
                    "pnl_percent": float(pnl_perc),
                    "side": side
                }
                
                positions.append(position_obj)
                
                print(f"   ✅ Added to positions array: {symbol} {side}")
                
            except Exception as pos_err:
                print(f"   ❌ Error processing position {idx + 1}: {pos_err}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*60}")
        print(f"✅ Total positions to return: {len(positions)}")
        print(f"{'='*60}\n")
        
        # Log positions for debugging
        if positions:
            for pos in positions:
                print(f"   • {pos['symbol']} {pos['side']}: ${pos['position_value']:.2f}")
        else:
            print("   (No open positions)")
        
        return positions

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ CRITICAL ERROR in get_positions_data()")
        print(f"{'='*60}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return []


def save_balance_history(balance):
    """Save balance to history (max 100 entries)"""
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Add new entry
        history.append({
            "timestamp": datetime.now().isoformat(),
            "balance": float(balance)
        })
        
        # Keep only last 100
        history = history[-100:]
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
            
    except Exception as e:
        print(f"⚠️ Error saving balance history: {e}")


def load_trades():
    """Load recent trades from file"""
    try:
        if TRADES_FILE.exists():
            with open(TRADES_FILE, 'r') as f:
                trades = json.load(f)
                return trades[-20:]  # Last 20 trades
        return []
    except Exception as e:
        print(f"⚠️ Error loading trades: {e}")
        return []


def save_trade(trade_data):
    """Save a completed trade"""
    try:
        if TRADES_FILE.exists():
            with open(TRADES_FILE, 'r') as f:
                trades = json.load(f)
        else:
            trades = []
        
        trades.append(trade_data)
        trades = trades[-100:]  # Keep last 100
        
        with open(TRADES_FILE, 'w') as f:
            json.dump(trades, f, indent=2)
        
        # Log trade to console
        symbol = trade_data.get('symbol', 'Unknown')
        side = trade_data.get('side', 'LONG')
        pnl = trade_data.get('pnl', 0)
        
        # Format log message
        side_emoji = "📈" if side == "LONG" else "📉"
        log_message = f"{side_emoji} Closed {side} {symbol} ${pnl:+.2f}"
        
        add_console_log(log_message, "trade")
            
    except Exception as e:
        print(f"⚠️ Error saving trade: {e}")

def log_position_open(symbol, side, size_usd):
    """Log when a position is opened"""
    try:
        emoji = "📈" if side == "LONG" else "📉"
        message = f"{emoji} Opened {side} {symbol} ${size_usd:.2f}"
        add_console_log(message, "trade")
    except Exception as e:
        print(f"⚠️ Error logging position open: {e}")

# ============================================================================
# CONSOLE LOGGING SUPPORT (enhanced for live updates)
# ============================================================================

# In-memory cache of recent console logs for instant visibility during agent_running/agent_executing
console_log_cache = []
console_log_lock = Lock()

def add_console_log(message, level="info"):
    """
    Add a log message to console and in-memory cache with thread safety.
    Ensures logs are visible immediately during agent_running and agent_executing.
    """
    global console_log_cache

    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "message": str(message),
        "level": level
    }

    try:
        # --- Thread-safe cache update ---
        with console_log_lock:
            console_log_cache.append(entry)
            console_log_cache = console_log_cache[-500:]  # keep last 500

        # --- Persist to file ---
        if CONSOLE_FILE.exists():
            with open(CONSOLE_FILE, 'r') as f:
                content = f.read().strip()
                logs = json.loads(content) if content else []
        else:
            logs = []

        logs.append(entry)
        logs = logs[-500:]
        with open(CONSOLE_FILE, 'w') as f:
            json.dump(logs, f, indent=2)

        # --- Always print and flush for terminal visibility ---
        print(f"[{entry['timestamp']}] {entry['message']}", flush=True)

    except Exception as e:
        print(f"⚠️ Error saving console log: {e}", flush=True)

# Redirect all print() output to also log to dashboard
import builtins
_original_print = builtins.print

def mirrored_print(*args, **kwargs):
    message = " ".join(str(a) for a in args)
    _original_print(*args, **kwargs)
    try:
        add_console_log(message, "info")
    except Exception:
        pass

builtins.print = mirrored_print



def get_console_logs():
    """Get console logs"""
    try:
        if CONSOLE_FILE.exists():
            with open(CONSOLE_FILE, 'r') as f:
                content = f.read()
                if not content.strip():
                    return []
                return json.loads(content)
        return []
    except json.JSONDecodeError as e:
        print(f"⚠️ Console log file corrupted, resetting: {e}")
        # Reset corrupted file
        with open(CONSOLE_FILE, 'w') as f:
            json.dump([], f)
        return []
    except Exception as e:
        print(f"⚠️ Error loading console logs: {e}")
        return []

def load_agent_state():
    """Load agent state from persistent storage"""
    try:
        if AGENT_STATE_FILE.exists():
            with open(AGENT_STATE_FILE, 'r') as f:
                return json.load(f)
        
        # Return default state if file doesn't exist
        return {
            "running": False,
            "last_started": None,
            "last_stopped": None,
            "total_cycles": 0
        }
    except Exception as e:
        print(f"⚠️ Error loading agent state: {e}")
        return {
            "running": False,
            "last_started": None,
            "last_stopped": None,
            "total_cycles": 0
        }


def save_agent_state(state):
    """Save agent state to persistent storage"""
    try:
        with open(AGENT_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving agent state: {e}")

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
                    cprint(f"❌ CRITICAL: Error getting balance: {e}", "red")
                    # Don't return 0, raise exception
                    raise RuntimeError(f"Failed to get HyperLiquid balance: {e}")

            return float(balance)
            
        else:
            # SOLANA
            balance = n.get_token_balance_usd(USDC_ADDRESS)
            return balance
            
    except Exception as e:
        cprint(f"❌ CRITICAL: Error getting account balance: {e}", "red")
        cprint("🛑 Cannot trade with unknown balance - stopping cycle", "red")
        import traceback
        traceback.print_exc()
        
        # Log to dashboard console
        try:
            import sys
            from pathlib import Path
            parent_dir = Path(__file__).parent.parent
            if str(parent_dir) not in sys.path:
                sys.path.insert(0, str(parent_dir))
            from trading_app import add_console_log
            add_console_log(f"❌ Cannot get account balance: {e}", "error")
        except:
            pass
        
        # RAISE exception instead of returning 0
        raise RuntimeError(f"Failed to get account balance: {e}")

# ============================================================================
# TRADING AGENT CONTROL
# ============================================================================

def run_trading_agent():
    """Run the trading agent in a loop with output capture"""
    global agent_running, stop_agent_flag, agent_executing
    
    add_console_log("Trading agent started", "success")
    
    while agent_running and not stop_agent_flag:
        try:
            add_console_log(f"Running analysis cycle", "info")
            
            # SET EXECUTION FLAG WITH LOCK
            with agent_lock:
                agent_executing = True
            
            # Capture start time
            cycle_start = time.time()
            
            # Import trading agent
            try:
                from src.agents.trading_agent import TradingAgent
            except ImportError:
                try:
                    from src.agents.trading_agent import TradingAgent
                except ImportError:
                    import sys
                    sys.path.insert(0, str(BASE_DIR / "src" / "agents"))
                    from trading_agent import TradingAgent
            
            # Create agent instance
            agent = TradingAgent()
            
            # Get tokens list
            if EXCHANGE in ["ASTER", "HYPERLIQUID"]:
                from src.agents.trading_agent import SYMBOLS as tokens
            else:
                from src.agents.trading_agent import MONITORED_TOKENS as tokens
            
            # Log analysis start
            add_console_log(f"\n🤖 Analyzing {len(tokens)} tokens", "info")
            
            # Run the trading cycle
            agent.run_trading_cycle()
            
            # Calculate cycle duration
            cycle_duration = int(time.time() - cycle_start)
            
            add_console_log(f"Cycle complete ({cycle_duration}s)", "success")

            # CLEAR EXECUTION FLAG WITH LOCK
            with agent_lock:
                agent_executing = False
            
            # Get recommendations summary
            if hasattr(agent, 'recommendations_df') and len(agent.recommendations_df) > 0:
                buy_count = len(agent.recommendations_df[agent.recommendations_df['action'] == 'BUY'])
                sell_count = len(agent.recommendations_df[agent.recommendations_df['action'] == 'SELL'])
                nothing_count = len(agent.recommendations_df[agent.recommendations_df['action'] == 'NOTHING'])
                
                add_console_log(f"Signals: {buy_count} BUY, {sell_count} SELL, {nothing_count} HOLD", "trade")

            from src.agents.trading_agent import SLEEP_BETWEEN_RUNS_MINUTES as minutes
            # Wait 60 minutes before next cycle
            add_console_log("✅ Finished Trading cycle...", "info")
            add_console_log("Next cycle starts in minutes", "info")
            
            # Wait with stop flag checking every minute
            for i in range(60):
                if stop_agent_flag:
                    add_console_log("Stop signal received", "info")
                    break
                time.sleep(60)
            
        except Exception as e:
            # RESET EXECUTING FLAG ON ERROR WITH LOCK
            with agent_lock:
                agent_executing = False
                
            error_msg = f"Cycle error: {str(e)}"
            add_console_log(error_msg, "error")
            import traceback
            traceback.print_exc()
            add_console_log("Retrying in 60 sec", "warning")
            time.sleep(60)
    
    # FINAL CLEANUP WITH LOCK
    with agent_lock:
        agent_running = False
        agent_executing = False
        
    add_console_log("Agent stopped", "info")

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

    
@app.route('/api/agent-status')
def get_agent_status():
    """Lightweight status check - returns if agent is actively executing"""
    global agent_running, agent_executing, agent_thread
    with agent_lock:
        # Also check if thread is actually alive
        thread_alive = agent_thread is not None and agent_thread.is_alive()
        
        # If thread died but flags say running, fix the flags
        if agent_running and not thread_alive:
            add_console_log("⚠️ Agent thread died unexpectedly - resetting flags", "warning")
            agent_running = False
            agent_executing = False
        
        return jsonify({
            "running": agent_running,
            "executing": agent_executing,
            "thread_alive": thread_alive,
            "timestamp": datetime.now().isoformat()
        })

@app.route('/api/data')
def get_data():
    """API endpoint for account data and positions"""
    try:
        account_data = get_account_data()
        positions = get_positions_data()
        
        response = {
            **account_data,
            "positions": positions,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in /api/data: {e}")
        return jsonify({
            "error": str(e),
            "account_balance": 0,
            "total_equity": 0,
            "pnl": 0,
            "positions": [],
            "status": "Error",
            "agent_running": False
        }), 500


@app.route('/api/trades')
def get_trades():
    """API endpoint for recent trades"""
    try:
        trades = load_trades()
        return jsonify(trades)
    except Exception as e:
        print(f"❌ Error in /api/trades: {e}")
        return jsonify([])


@app.route('/api/history')
def get_history():
    """API endpoint for balance history"""
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
                return jsonify(history)
        return jsonify([])
    except Exception as e:
        print(f"❌ Error in /api/history: {e}")
        return jsonify([])


@app.route('/api/console')
def get_console():
    """Return console logs, including in-memory cache for live updates."""
    try:
        with console_log_lock:
            cached = list(console_log_cache)
        if CONSOLE_FILE.exists():
            with open(CONSOLE_FILE, 'r') as f:
                content = f.read().strip()
                file_logs = json.loads(content) if content else []
        else:
            file_logs = []
        merged = (file_logs + cached)[-500:]
        return jsonify(merged)
    except Exception as e:
        print(f"⚠️ Error reading console logs: {e}", flush=True)
        return jsonify([])



@app.route('/api/start', methods=['POST'])
def start_agent():
    """Start the trading agent"""
    global agent_thread, agent_running, stop_agent_flag
    
    # USE LOCK FOR ENTIRE START OPERATION
    with agent_lock:
        if agent_running:
            return jsonify({
                "status": "already_running",
                "message": "Agent is already running"
            })
        
        agent_running = True
        stop_agent_flag = False
        
        # Save state with timestamp
        state = load_agent_state()
        state["running"] = True
        state["last_started"] = datetime.now().isoformat()
        state["total_cycles"] = state.get("total_cycles", 0) + 1
        save_agent_state(state)
        
        # Start agent thread
        agent_thread = threading.Thread(target=run_trading_agent, daemon=True)
        agent_thread.start()
    
    add_console_log("Trading agent started via dashboard", "success")
    
    return jsonify({
        "status": "started",
        "message": "Trading agent started successfully"
    })
    
@app.route('/api/stop', methods=['POST'])
def stop_agent():
    """Stop the trading agent"""
    global agent_running, stop_agent_flag
    
    # USE LOCK FOR ENTIRE STOP OPERATION
    with agent_lock:
        if not agent_running:
            return jsonify({
                "status": "not_running",
                "message": "Agent is not running"
            })
        
        stop_agent_flag = True
        agent_running = False
        
        # Save state with timestamp
        state = load_agent_state()
        state["running"] = False
        state["last_stopped"] = datetime.now().isoformat()
        save_agent_state(state)
    
    add_console_log("Trading agent stop requested via dashboard", "info")
    
    return jsonify({
        "status": "stopped",
        "message": "Trading agent stopped successfully"
    })


@app.route('/health')
def health_check():
    """Health check endpoint for EasyPanel"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/api/debug-status')
def debug_status():
    """Detailed debugging status endpoint"""
    with agent_lock:
        return jsonify({
            "agent_running": agent_running,
            "agent_executing": agent_executing,
            "stop_agent_flag": stop_agent_flag,
            "shutdown_in_progress": shutdown_in_progress,
            "thread_exists": agent_thread is not None,
            "thread_alive": agent_thread.is_alive() if agent_thread else False,
            "thread_daemon": agent_thread.daemon if agent_thread else None,
            "exchange_connected": EXCHANGE_CONNECTED,
            "exchange_type": EXCHANGE,
            "timestamp": datetime.now().isoformat()
        })
 
# ============================================================================
# GRACEFUL SHUTDOWN HANDLER
# ============================================================================

def cleanup_and_exit(signum=None, frame=None):
    """
    Graceful shutdown handler - ALWAYS releases port 5000
    Called on Ctrl+C or kill signal
    """
    global agent_running, stop_agent_flag, shutdown_in_progress
    
    # Prevent multiple shutdown attempts
    if shutdown_in_progress:
        return
    
    shutdown_in_progress = True
    
    print("\n\n" + "="*60)
    print("🛑 SHUTDOWN SIGNAL RECEIVED")
    print("="*60)
    
    # Stop trading agent if running
    if agent_running:
        print("⏹️  Stopping trading agent...")
        stop_agent_flag = True
        agent_running = False
        
        # Wait for agent thread to finish (max 5 seconds)
        if agent_thread and agent_thread.is_alive():
            print("   Waiting for agent thread to finish...")
            agent_thread.join(timeout=5)
        
        # Save final state
        try:
            state = load_agent_state()
            state["running"] = False
            state["last_stopped"] = datetime.now().isoformat()
            save_agent_state(state)
            add_console_log("Agent stopped - server shutting down", "info")
            print("   ✅ Agent stopped and state saved")
        except Exception as e:
            print(f"   ⚠️  Error saving agent state: {e}")
    else:
        print("ℹ️  Trading agent was not running")
    
    # Log shutdown
    try:
        add_console_log("Dashboard server shutting down", "info")
    except Exception:
        pass
    
    print("\n✅ Cleanup complete - Port 5000 released")
    print("="*60)
    print("👋 Goodbye! You can restart immediately.\n")
    
    # Force exit to ensure port is released
    os._exit(0)


# Register shutdown handlers
signal.signal(signal.SIGINT, cleanup_and_exit)   # Ctrl+C
signal.signal(signal.SIGTERM, cleanup_and_exit)  # kill command
atexit.register(lambda: cleanup_and_exit() if not shutdown_in_progress else None)


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    
    print(f"""
{'='*60}
Marco's AI Trading Dashboard
{'='*60}
Dashboard URL: http://0.0.0.0:{port}
Local URL: http://localhost:{port}
Exchange: HyperLiquid
Status: {'Connected ✅' if EXCHANGE_CONNECTED else 'Demo Mode ⚠️'}
Agent: {'Running 🟢' if agent_running else 'Stopped 🔴'}
{'='*60}

Press Ctrl+C to shutdown gracefully
Port {port} will be released immediately on exit
""")
    
    add_console_log("Dashboard server started", "info")
    
    if not EXCHANGE_CONNECTED:
        add_console_log("Running in DEMO mode - HyperLiquid not connected", "warning")
    
    try:
        # Run Flask with proper settings for clean shutdown
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        cleanup_and_exit()
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        cleanup_and_exit()
