#!/usr/bin/env python3
"""
Trading Dashboard Backend
=========================
Production-ready Flask app for HyperLiquid trading
"""

import os
import sys
import json
import time
import threading
import queue
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from dotenv import load_dotenv
from flask_cors import CORS
import signal
import atexit
from functools import wraps

# ============================================================================
# SETUP & CONFIGURATION
# ============================================================================

# 🦈 EXCHANGE SELECTION (Default, will be overridden by agent config)
EXCHANGE = "HYPERLIQUID"  # Options: "ASTER", "HYPERLIQUID", "SOLANA"

# Add project root to Python path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Import shared logging utility (prevents circular imports)
from src.utils.logging_utils import add_console_log, log_queue, log_position_open
from src.utils.settings_manager import (
    load_settings,
    save_settings,
    validate_settings,
    get_available_models_for_provider,
    get_hyperliquid_tokens,
    get_all_token_symbols
)

# Load environment variables
load_dotenv()

# Initialize Flask with correct paths
DASHBOARD_DIR = BASE_DIR / "dashboard"
app = Flask(
    __name__,
    template_folder=str(DASHBOARD_DIR / "templates"),
    static_folder=str(DASHBOARD_DIR / "static"),
    static_url_path="/static"
)

# Configure session (uses Flask's built-in server-side sessions)
# SECURITY: Secret key MUST be set in .env file for production!
flask_secret = os.getenv('FLASK_SECRET_KEY')
if not flask_secret:
    print("⚠️ WARNING: FLASK_SECRET_KEY not set! Using insecure default.")
    print("⚠️ Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")
    flask_secret = 'INSECURE-DEFAULT-KEY-CHANGE-ME'

app.config['SECRET_KEY'] = flask_secret
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Login credentials (loaded from environment variables for security)
VALID_CREDENTIALS = {
    'username': os.getenv('DASHBOARD_USERNAME', ''),
    'email': os.getenv('DASHBOARD_EMAIL', ''),
    'password': os.getenv('DASHBOARD_PASSWORD', '')
}

# Validate credentials are set
if not all(VALID_CREDENTIALS.values()):
    print("⚠️ WARNING: Dashboard credentials not fully configured in .env!")
    print("⚠️ Set DASHBOARD_USERNAME, DASHBOARD_EMAIL, and DASHBOARD_PASSWORD")

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
agent_executing = False  # True when actively analyzing, False when waiting between cycles
stop_agent_flag = False
shutdown_in_progress = False
stop_event = threading.Event()  # Event for clean shutdown signaling

# Thread synchronization
state_lock = threading.Lock()  # Lock for agent state variables
# log_queue imported from src.utils.logging_utils
log_writer_thread = None
log_writer_running = False

# Symbols list (for trading agent reference)
SYMBOLS = [
    'ETH',        # Ethereum
    'BTC',        # Bitcoin
    'SOL',        # Solana
    'AAVE',       # Aave
    'LINK',       # Chainlink
    'LTC',        # Litecoin
    'HYPE',       # Hyperliquid Exchange Token
    'FARTCOIN',   # FartCoin
]

# ============================================================================
# LOGGING UTILITIES
# ============================================================================

def rotate_log_files(log_dir, prefix, max_files=5, max_size_kb=300):
    """Rotate log files, keeping only the most recent max_files with max size."""
    import os

    # Get all log files matching the pattern
    log_files = sorted([f for f in log_dir.glob(f"{prefix}_*.log")],
                      key=lambda x: x.stat().st_mtime, reverse=True)

    # Remove old files if we exceed max_files
    if len(log_files) >= max_files:
        for old_file in log_files[max_files-1:]:
            try:
                old_file.unlink()
            except Exception as e:
                print(f"⚠️ Failed to remove old log file {old_file}: {e}")

    # Check size of current log file
    if log_files:
        current_log = log_files[0]
        size_kb = current_log.stat().st_size / 1024

        if size_kb > max_size_kb:
            # Create new log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return log_dir / f"{prefix}_{timestamp}.log"

    # Return current or new log file
    if log_files and log_files[0].stat().st_size < max_size_kb * 1024:
        return log_files[0]
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return log_dir / f"{prefix}_{timestamp}.log"


def log_writer_worker():
    """Background thread that batches log writes to avoid I/O bottleneck with rotating logs."""
    global log_writer_running

    log_buffer = []
    last_write_time = time.time()
    WRITE_INTERVAL = 2.0  # Write to disk every 2 seconds

    # Local cache directory (in repo, not on server disk)
    CACHE_DIR = BASE_DIR / ".cache" / "logs"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Add to .gitignore
    gitignore_file = BASE_DIR / ".gitignore"
    if gitignore_file.exists():
        with open(gitignore_file, 'r') as f:
            content = f.read()
        if '.cache/' not in content:
            with open(gitignore_file, 'a') as f:
                f.write('\n# Local cache directory\n.cache/\n')

    while log_writer_running:
        try:
            # Try to get logs from queue with timeout
            try:
                log_entry = log_queue.get(timeout=0.5)
                log_buffer.append(log_entry)
                log_queue.task_done()
            except queue.Empty:
                pass

            # Write to disk if buffer has entries and interval elapsed
            current_time = time.time()
            if log_buffer and (current_time - last_write_time >= WRITE_INTERVAL):
                # 1. Write to console_logs.json (last 200 for dashboard)
                if CONSOLE_FILE.exists():
                    try:
                        with open(CONSOLE_FILE, 'r') as f:
                            logs = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        logs = []
                else:
                    logs = []

                # Append buffered logs
                logs.extend(log_buffer)

                # Keep last 200 entries
                logs = logs[-200:]

                # Write to disk
                with open(CONSOLE_FILE, 'w') as f:
                    json.dump(logs, f, indent=2)

                # 2. Append to rotating log files (max 5 files, 300KB each)
                log_file = rotate_log_files(CACHE_DIR, "app", max_files=5, max_size_kb=300)

                with open(log_file, 'a') as f:
                    for entry in log_buffer:
                        log_line = f"[{entry['timestamp']}] [{entry['level'].upper()}] {entry['message']}\n"
                        f.write(log_line)

                # Clear buffer and update timestamp
                log_buffer.clear()
                last_write_time = current_time

        except Exception as e:
            print(f"⚠️ Log writer error: {e}")
            time.sleep(1)

    # Final flush on shutdown
    if log_buffer:
        try:
            # Write to console_logs.json
            if CONSOLE_FILE.exists():
                with open(CONSOLE_FILE, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            logs.extend(log_buffer)
            logs = logs[-200:]

            with open(CONSOLE_FILE, 'w') as f:
                json.dump(logs, f, indent=2)

            # Write to rotating log file
            log_file = rotate_log_files(CACHE_DIR, "app", max_files=5, max_size_kb=300)

            with open(log_file, 'a') as f:
                for entry in log_buffer:
                    log_line = f"[{entry['timestamp']}] [{entry['level'].upper()}] {entry['message']}\n"
                    f.write(log_line)

        except Exception as e:
            print(f"⚠️ Final log flush error: {e}")


# add_console_log function now imported from src.utils.logging_utils
# This prevents circular imports and fixes the broken log reference bug

# ============================================================================
# IMPORT TRADING FUNCTIONS (Favoring src module)
# ============================================================================
EXCHANGE_CONNECTED = False
try:
    # 1. Prioritize importing from the src module
    from src import nice_funcs_hyperliquid as n
    from eth_account import Account

    def _get_account():
        """Standardized key lookup for dashboard and agent"""
        key = os.getenv("HYPER_LIQUID_ETH_PRIVATE_KEY", "")
        clean_key = key.strip().replace('"', '').replace("'", "")
        if not clean_key:
            raise ValueError("HYPER_LIQUID_ETH_PRIVATE_KEY missing in .env")
        return Account.from_key(clean_key)

    EXCHANGE_CONNECTED = True
    print("✅ HyperLiquid functions loaded")

except ImportError:
    try:
        # 2. Fallback: Try importing from root nice_funcs_hyperliquid
        import nice_funcs_hyperliquid as n
        from eth_account import Account

        def _get_account():
            key = os.getenv("HYPER_LIQUID_ETH_PRIVATE_KEY", "")
            clean_key = key.strip().replace('"', '').replace("'", "")
            return Account.from_key(clean_key)

        EXCHANGE_CONNECTED = True
        print("✅ HyperLiquid functions loaded from root nice_funcs_hyperliquid")

    except ImportError as e:
        print(f"⚠️ Warning: Could not import HyperLiquid functions: {e}")
        print("⚠️ Dashboard will run in DEMO mode with simulated data")

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

# log_position_open function now imported from src.utils.logging_utils


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

# ============================================================================
# TRADING AGENT CONTROL
# ============================================================================

def should_stop_agent():
    """Check if agent should stop - used as callback for trading agent"""
    with state_lock:
        return stop_agent_flag or not agent_running


def run_trading_agent():
    """Run the trading agent in a loop with output capture"""
    global agent_running, agent_executing, stop_agent_flag

    add_console_log("AI Trading agent started", "success")

    # Load user settings
    user_settings = load_settings()

    # Get monitored tokens from settings (use user's selection, not hardcoded)
    monitored_tokens = user_settings.get('monitored_tokens', ['ETH', 'BTC', 'SOL'])
    swarm_mode = user_settings.get('swarm_mode', 'single')
    mode_display = 'Swarm' if swarm_mode == 'swarm' else 'Single Agent'

    add_console_log(f"Settings: {user_settings.get('timeframe')} timeframe, {user_settings.get('days_back')} days, {user_settings.get('sleep_minutes')} min cycle", "info")
    add_console_log(f"Mode: {mode_display} | Tokens: {', '.join(monitored_tokens)}", "info")
    add_console_log(f"AI Model: {user_settings.get('ai_provider')}/{user_settings.get('ai_model')}", "info")

    # Import trading agent at the top of the function
    try:
        from src.agents.trading_agent import TradingAgent, EXCHANGE
        trading_agent_module = "src.agents.trading_agent"
    except ImportError:
        try:
            from trading_agent import TradingAgent, EXCHANGE
            trading_agent_module = "trading_agent"
        except ImportError:
            import sys
            sys.path.insert(0, str(BASE_DIR / "src" / "agents"))
            from trading_agent import TradingAgent, EXCHANGE
            trading_agent_module = "trading_agent (sys.path)"

    add_console_log("Loaded trading_agent", "info")
    add_console_log(f"Using exchange {EXCHANGE}", "info")

    # Convert minutes to seconds for sleep (use user setting)
    sleep_seconds = user_settings.get('sleep_minutes', 30) * 60

    while True:
        # Check stop condition with lock
        with state_lock:
            if not agent_running or stop_agent_flag:
                break

        try:
            add_console_log(f"Running analysis cycle", "info")

            # Capture start time
            cycle_start = time.time()

            # Reload settings in case they changed
            user_settings = load_settings()
            monitored_tokens = user_settings.get('monitored_tokens', ['ETH', 'BTC', 'SOL'])

            # Create agent instance with user settings and stop callback
            agent = TradingAgent(
                timeframe=user_settings.get('timeframe', '30m'),
                days_back=user_settings.get('days_back', 2),
                stop_check_callback=should_stop_agent,
                # Pass user-selected tokens to the agent
                symbols=monitored_tokens,
                # Pass AI settings
                ai_provider=user_settings.get('ai_provider', 'gemini'),
                ai_model=user_settings.get('ai_model', 'gemini-2.5-flash'),
                ai_temperature=user_settings.get('ai_temperature', 0.3),
                ai_max_tokens=user_settings.get('ai_max_tokens', 2000)
            )

            # Set executing flag to True (agent is now actively analyzing)
            with state_lock:
                agent_executing = True

            # Run the trading cycle (will check stop callback periodically)
            agent.run_trading_cycle()

            # Set executing flag back to False (analysis complete, entering wait phase)
            with state_lock:
                agent_executing = False

            # Check if stopped mid-cycle
            if should_stop_agent():
                add_console_log("Agent stopped mid-cycle", "info")
                break

            # Calculate cycle duration
            cycle_duration = int(time.time() - cycle_start)

            add_console_log(f"Cycle complete ({cycle_duration}s)", "success")

            # Get recommendations summary
            if hasattr(agent, 'recommendations_df') and len(agent.recommendations_df) > 0:
                buy_count = len(agent.recommendations_df[agent.recommendations_df['action'] == 'BUY'])
                sell_count = len(agent.recommendations_df[agent.recommendations_df['action'] == 'SELL'])
                nothing_count = len(agent.recommendations_df[agent.recommendations_df['action'] == 'NOTHING'])

                add_console_log(f"Signals: {buy_count} BUY, {sell_count} SELL, {nothing_count} HOLD", "trade")

            # Wait before next cycle
            add_console_log("Finished trading cycle", "info")
            add_console_log(f"Next cycle starts in {user_settings.get('sleep_minutes', 30)} minutes", "info")

            # Use Event.wait() instead of blocking sleep for responsive shutdown
            if stop_event.wait(timeout=sleep_seconds):
                add_console_log("Stop signal received via event", "info")
                break

        except Exception as e:
            # Reset executing flag on error
            with state_lock:
                agent_executing = False

            error_msg = f"Cycle error: {str(e)}"
            add_console_log(error_msg, "error")
            import traceback
            traceback.print_exc()
            add_console_log("Retrying in 60 sec", "warning")

            # Wait with interruptible sleep
            if stop_event.wait(timeout=60):
                add_console_log("Stop signal received during error recovery", "info")
                break

    # Clean shutdown
    with state_lock:
        agent_running = False
        agent_executing = False
    add_console_log("Agent stopped", "info")

# ============================================================================
# AUTHENTICATION
# ============================================================================

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            # For API routes, return JSON error instead of redirect
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required', 'redirect': '/login'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/login', methods=['GET'])
def login():
    """Serve the login page"""
    # If already logged in, redirect to dashboard
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle login requests"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    # Check credentials (username OR email, and password)
    if ((username == VALID_CREDENTIALS['username'] or
         username == VALID_CREDENTIALS['email']) and
        password == VALID_CREDENTIALS['password']):

        session['logged_in'] = True
        session['username'] = VALID_CREDENTIALS['username']
        add_console_log(f"User {VALID_CREDENTIALS['username']} logged in", "success")

        return jsonify({
            'success': True,
            'message': 'Login successful'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        }), 401


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Handle logout requests"""
    username = session.get('username', 'Unknown')
    session.clear()
    add_console_log(f"User {username} logged out", "info")

    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })


@app.route('/')
@login_required
def index():
    """Serve the main dashboard"""
    return render_template('index.html')


@app.route('/api/data')
@login_required
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
@login_required
def get_trades():
    """API endpoint for recent trades"""
    try:
        trades = load_trades()
        return jsonify(trades)
    except Exception as e:
        print(f"❌ Error in /api/trades: {e}")
        return jsonify([])


@app.route('/api/history')
@login_required
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
@login_required
def get_console():
    """API endpoint for console logs"""
    try:
        logs = get_console_logs()
        return jsonify(logs)
    except Exception as e:
        print(f"❌ Error in /api/console: {e}")
        return jsonify([])


@app.route('/api/start', methods=['POST'])
@login_required
def start_agent():
    """Start the trading agent"""
    global agent_thread, agent_running, stop_agent_flag

    with state_lock:
        if agent_running:
            return jsonify({
                "status": "already_running",
                "message": "Agent is already running"
            })

        agent_running = True
        stop_agent_flag = False
        stop_event.clear()  # Clear the stop event

        # Save state
        state = load_agent_state()
        state["running"] = True
        state["last_started"] = datetime.now().isoformat()
        state["total_cycles"] = state.get("total_cycles", 0) + 1
        save_agent_state(state)

        agent_thread = threading.Thread(target=run_trading_agent, daemon=True)
        agent_thread.start()

    return jsonify({
        "status": "started",
        "message": "Trading agent started successfully"
    })


@app.route('/api/stop', methods=['POST'])
@login_required
def stop_agent():
    """Stop the trading agent"""
    global agent_running, stop_agent_flag

    with state_lock:
        if not agent_running:
            return jsonify({
                "status": "not_running",
                "message": "Agent is not running"
            })

        stop_agent_flag = True
        agent_running = False
        stop_event.set()  # Signal stop event

        state = load_agent_state()
        state["running"] = False
        state["last_stopped"] = datetime.now().isoformat()
        save_agent_state(state)

    add_console_log("Trading agent stop requested via dashboard", "info")

    return jsonify({
        "status": "stopped",
        "message": "Trading agent stopped successfully"
    })


@app.route('/api/status')
@login_required
def get_status():
    """Get current agent and exchange status"""
    state = load_agent_state()
    return jsonify({
        "running": agent_running,
        "connected": EXCHANGE_CONNECTED,
        "last_started": state.get("last_started"),
        "last_stopped": state.get("last_stopped"),
        "total_cycles": state.get("total_cycles", 0),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/agent-status')
@login_required
def get_agent_status():
    """Return current agent status and metadata."""
    try:
        state = load_agent_state()
        status = {
            "agent_running": agent_running,
            "executing": agent_executing,  # True when actively analyzing
            "stop_requested": stop_agent_flag,
            "last_started": state.get("last_started"),
            "last_stopped": state.get("last_stopped"),
            "total_cycles": state.get("total_cycles", 0),
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(status)
    except Exception as e:
        print(f"❌ Error in /api/agent-status: {e}")
        return jsonify({
            "agent_running": False,
            "error": str(e)
        }), 500


@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Get or update user settings"""
    if request.method == 'GET':
        # Load and return current settings
        user_settings = load_settings()
        return jsonify({
            'success': True,
            'settings': user_settings
        })
    else:
        # Update settings
        try:
            data = request.get_json()

            # Validate settings
            valid, errors = validate_settings(data)
            if not valid:
                return jsonify({
                    'success': False,
                    'message': 'Invalid settings',
                    'errors': errors
                }), 400

            # Save settings
            if save_settings(data):
                # Build detailed log message
                log_parts = [
                    f"Timeframe={data.get('timeframe')}",
                    f"Days Back={data.get('days_back')}",
                    f"Sleep={data.get('sleep_minutes')} min"
                ]

                # Add AI model info if present
                if 'ai_provider' in data and 'ai_model' in data:
                    log_parts.append(f"AI={data.get('ai_provider')}/{data.get('ai_model')}")

                add_console_log(f"Settings updated: {', '.join(log_parts)}", "info")

                return jsonify({
                    'success': True,
                    'message': 'Settings saved successfully',
                    'settings': data
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to save settings'
                }), 500

        except Exception as e:
            print(f"❌ Error updating settings: {e}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500


@app.route('/api/ai-models', methods=['GET'])
@login_required
def get_ai_models():
    """
    Get available AI models for all providers or a specific provider
    Query param: ?provider=gemini (optional)
    """
    try:
        provider = request.args.get('provider')

        if provider:
            # Get models for specific provider
            models = get_available_models_for_provider(provider)
            if not models:
                return jsonify({
                    'success': False,
                    'message': f'Invalid provider: {provider}'
                }), 400

            return jsonify({
                'success': True,
                'provider': provider,
                'models': models
            })
        else:
            # Get all providers and their models
            all_providers = ['anthropic', 'openai', 'gemini', 'deepseek', 'xai',
                           'mistral', 'cohere', 'perplexity', 'groq', 'ollama', 'openrouter']

            all_models = {}
            for p in all_providers:
                all_models[p] = get_available_models_for_provider(p)

            return jsonify({
                'success': True,
                'providers': all_providers,
                'models': all_models
            })

    except Exception as e:
        print(f"❌ Error getting AI models: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/tokens', methods=['GET'])
@login_required
def get_tokens():
    """
    Get available Hyperliquid tokens organized by category
    Returns categorized tokens (crypto, altcoins, memecoins)
    """
    try:
        tokens = get_hyperliquid_tokens()
        all_symbols = get_all_token_symbols()

        return jsonify({
            'success': True,
            'categories': tokens,
            'all_symbols': all_symbols,
            'total_count': len(all_symbols)
        })

    except Exception as e:
        print(f"❌ Error getting tokens: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint for EasyPanel"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200

# ============================================================================
# GRACEFUL SHUTDOWN HANDLER
# ============================================================================

def cleanup_and_exit(signum=None, frame=None):
    """Graceful shutdown handler."""
    global agent_running, stop_agent_flag, shutdown_in_progress, log_writer_running

    if shutdown_in_progress:
        return
    shutdown_in_progress = True

    print("\n\n" + "=" * 60)
    print("🛑 SHUTDOWN SIGNAL RECEIVED")
    print("=" * 60)

    # Stop trading agent
    with state_lock:
        if agent_running:
            print("⏹️  Stopping trading agent...")
            stop_agent_flag = True
            agent_running = False
            stop_event.set()  # Signal stop event

    if agent_thread and agent_thread.is_alive():
        print("   Waiting for agent thread to finish...")
        agent_thread.join(timeout=10)  # Increased timeout to 10 seconds

        if agent_thread.is_alive():
            print("   ⚠️  Agent thread still running after timeout")
        else:
            print("   ✅ Agent thread stopped")

    # Save final state
    try:
        state = load_agent_state()
        state["running"] = False
        state["last_stopped"] = datetime.now().isoformat()
        save_agent_state(state)
        add_console_log("Agent stopped - server shutting down", "info")
        print("   ✅ Agent state saved")
    except Exception as e:
        print(f"   ⚠️  Error saving agent state: {e}")

    # Stop log writer thread
    print("⏹️  Stopping log writer...")
    log_writer_running = False

    if log_writer_thread and log_writer_thread.is_alive():
        print("   Waiting for log writer to flush...")
        log_writer_thread.join(timeout=5)

        if log_writer_thread.is_alive():
            print("   ⚠️  Log writer still running after timeout")
        else:
            print("   ✅ Log writer stopped")

    try:
        add_console_log("Dashboard server shutting down", "info")
        # Give a moment for final log to be queued
        time.sleep(0.5)
    except Exception:
        pass

    print("\n✅ Cleanup complete - Port 5000 released")
    print("=" * 60)
    print("👋 Goodbye! You can restart immediately.\n")

    os._exit(0)


signal.signal(signal.SIGINT, cleanup_and_exit)
signal.signal(signal.SIGTERM, cleanup_and_exit)
atexit.register(lambda: cleanup_and_exit() if not shutdown_in_progress else None)

# ============================================================================
# STARTUP SECTION
# ============================================================================

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.getenv('PORT', 5000))

    # Start log writer thread
    print("🚀 Starting async log writer...")
    log_writer_running = True
    log_writer_thread = threading.Thread(target=log_writer_worker, daemon=True)
    log_writer_thread.start()
    print("✅ Log writer started")

    # Startup Banner for Terminal
    print(f"""
{'=' * 60}
AI Trading Dashboard
{'=' * 60}
Dashboard URL: http://0.0.0.0:{port}
Local URL:     http://localhost:{port}
Exchange:      HyperLiquid
Status:        {'Connected ✅' if EXCHANGE_CONNECTED else 'Demo Mode ⚠️'}
Agent Status:  {'Running 🟢' if agent_running else 'Stopped 🔴'}
{'=' * 60}
Press Ctrl+C to shutdown gracefully
""")

    # Log startup messages
    add_console_log("Dashboard server started", "info")

    # Log a warning if the exchange functions failed to load
    if not EXCHANGE_CONNECTED:
        add_console_log("Running in DEMO mode - HyperLiquid not connected", "warning")

    try:
        # Run the Flask production server
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully using the cleanup function
        cleanup_and_exit()
    except Exception as e:
        # Log any unexpected server errors
        print(f"\n❌ Server error: {e}")
        cleanup_and_exit()
