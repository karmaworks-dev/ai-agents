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
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from flask_cors import CORS

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

# ============================================================================
# IMPORT TRADING FUNCTIONS (with fallback)
# ============================================================================

EXCHANGE_CONNECTED = False

try:
    # Try importing from nice_funcs.py (local file)
    import nice_funcs_hyperliquid as n
    from eth_account import Account
    
    def _get_account():
        """Get HyperLiquid account from environment"""
        key = os.getenv("HYPERLIQUID_KEY", "")
        clean_key = key.strip().replace('"', '').replace("'", "")
        return Account.from_key(clean_key)
    
    EXCHANGE_CONNECTED = True
    print("✅ HyperLiquid functions loaded from nice_funcs.py")
    
except ImportError:
    try:
        # Fallback: Try importing from src module
        from src import nice_funcs_hyperliquid as n
        from eth_account import Account
        
        def _get_account():
            key = os.getenv("HYPERLIQUID_KEY", "")
            clean_key = key.strip().replace('"', '').replace("'", "")
            return Account.from_key(clean_key)
        
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
    """Fetch live open positions from HyperLiquid (ignore saved trades)"""
    if not EXCHANGE_CONNECTED or n is None:
        # Return empty list if exchange is disconnected or in demo mode
        return []

    try:
        # Get the Account object
        account = _get_account()

        # Import symbols from config, fallback to defaults
        try:
            from src.config import HYPERLIQUID_SYMBOLS as SYMBOLS
        except ImportError:
            SYMBOLS = ['BTC', 'ETH', 'SOL', 'LTC']

        positions = []

        for symbol in SYMBOLS:
            try:
                # Fetch live position from the exchange
                pos_data = n.get_position(symbol, account)
                # Unpack the returned tuple
                _, im_in_pos, pos_size, _, entry_px, pnl_perc, is_long = pos_data

                if im_in_pos and pos_size != 0:
                    # Fetch current mark price
                    try:
                        ask, bid, _ = n.ask_bid(symbol)
                        mark_price = (ask + bid) / 2
                    except Exception as price_err:
                        print(f"⚠️ Error fetching mark price for {symbol}: {price_err}")
                        # Fallback to entry price if market data unavailable
                        mark_price = float(entry_px)
                    
                    # Calculate position value in USD
                    position_value = abs(float(pos_size)) * mark_price
                    
                    positions.append({
                        "symbol": symbol,
                        "size": float(pos_size),
                        "entry_price": float(entry_px),
                        "mark_price": float(mark_price),           # NEW
                        "position_value": float(position_value),   # NEW
                        "pnl_percent": float(pnl_perc),
                        "side": "LONG" if is_long else "SHORT"
                    })

            except Exception:
                # Skip symbols with no position or errors
                continue

        return positions

    except Exception as e:
        print(f"❌ Error fetching positions from exchange: {e}")
        import traceback
        traceback.print_exc()
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


def add_console_log(message, level="info"):
    """
    Add a log message to console with level support
    Args:
        message (str): Log message text
        level (str): Log level - "info", "success", "error", "warning", "trade"
    """
    try:
        if CONSOLE_FILE.exists():
            with open(CONSOLE_FILE, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "message": str(message),
            "level": level
        })
        
        logs = logs[-50:]  # Keep last 50 logs
        
        with open(CONSOLE_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
            
        # Also print to console
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    except Exception as e:
        print(f"⚠️ Error saving console log: {e}")


def get_console_logs():
    """Get console logs"""
    try:
        if CONSOLE_FILE.exists():
            with open(CONSOLE_FILE, 'r') as f:
                return json.load(f)
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

def run_trading_agent():
    """Run the trading agent in a loop"""
    global agent_running, stop_agent_flag
    
    add_console_log("Trading agent started", "success")
    
    while agent_running and not stop_agent_flag:
        try:
            add_console_log(f"Running cycle at {datetime.now().strftime('%H:%M:%S')}", "info")
            
            # Try multiple import paths
            try:
                # Try src.agents.trading_agent first
                from src.agents.trading_agent import TradingAgent
            except ImportError:
                try:
                    # Try root level trading_agent
                    from trading_agent import TradingAgent
                except ImportError:
                    # Last resort: import from current directory
                    import sys
                    sys.path.insert(0, str(BASE_DIR / "src" / "agents"))
                    from trading_agent import TradingAgent
            
            agent = TradingAgent()
            agent.run_trading_cycle()
            
            add_console_log("Cycle complete", "success")
            
            # Wait 60 minutes (checking stop flag every minute)
            add_console_log("⏳Next cycle in 60 min", "info")
            for i in range(60):
                if stop_agent_flag:
                    add_console_log("Stop signal received", "info")
                    break
                time.sleep(60)
            
        except Exception as e:
            error_msg = f"Cycle error: {str(e)}"
            add_console_log(error_msg, "error")
            import traceback
            traceback.print_exc()  # This will show full error
            add_console_log("Retrying in 60 sec", "warning")
            time.sleep(60)
    
    agent_running = False
    add_console_log("Agent stopped", "info")

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')


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
    """API endpoint for console logs"""
    try:
        logs = get_console_logs()
        return jsonify(logs)
    except Exception as e:
        print(f"❌ Error in /api/console: {e}")
        return jsonify([])


@app.route('/api/start', methods=['POST'])
def start_agent():
    """Start the trading agent"""
    global agent_thread, agent_running, stop_agent_flag
    
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

@app.route('/api/status')
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


@app.route('/health')
def health_check():
    """Health check endpoint for EasyPanel"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    
    print(f"""
{'='*60}
🌙 Moon Dev's Trading Dashboard
{'='*60}
Dashboard URL: http://0.0.0.0:{port}
Exchange: HyperLiquid
Status: {'Connected ✅' if EXCHANGE_CONNECTED else 'Demo Mode ⚠️'}
Agent: {'Running 🟢' if agent_running else 'Stopped 🔴'}
{'='*60}
""")
    
    add_console_log("🌐 Dashboard server started")
    
    if not EXCHANGE_CONNECTED:
        add_console_log("⚠️ Running in DEMO mode - HyperLiquid not connected")
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
