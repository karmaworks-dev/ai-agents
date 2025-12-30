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
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from flask_cors import CORS
import signal
import atexit

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
app = Flask(
    __name__,
    template_folder=str(DASHBOARD_DIR / "templates"),
    static_folder=str(DASHBOARD_DIR / "static"),
    static_url_path="/static"
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
shutdown_in_progress = False

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
    print("✅ HyperLiquid functions loaded from src.nice_funcs_hyperliquid")

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
# LOGGING UTILITIES
# ============================================================================

    def add_console_log(message, level="info"):
        """Write log message to console_logs.json and print to stdout."""
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

            logs = logs[-200:]  # Keep last 200 entries
            with open(CONSOLE_FILE, 'w') as f:
                json.dump(logs, f, indent=2)

            # Also print to console
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

        except Exception as e:
            print(f"⚠️ Logging error: {e}")

    # ============================================================================
    # AGENT STATE UTILITIES
    # ============================================================================

    def load_agent_state():
        """Load agent state from persistent storage"""
        try:
            if AGENT_STATE_FILE.exists():
                with open(AGENT_STATE_FILE, 'r') as f:
                    return json.load(f)
             # Default if file missing
            return {
                "running": False,
                "last_started": None,
                "last_stopped": None,
                "total_cycles": 0
            }
        except Exception as e:
            add_console_log(f"⚠️ Error loading agent state: {e}", "error")
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
            add_console_log(f"⚠️ Error saving agent state: {e}", "error")



    def _get_account():
        """Get HyperLiquid account from environment"""
        key = os.getenv("HYPER_LIQUID_ETH_PRIVATE_KEY", "")
        clean_key = key.strip().replace('"', '').replace("'", "")
        return Account.from_key(clean_key)

    EXCHANGE_CONNECTED = True
    print("✅ HyperLiquid functions loaded from nice_funcs_hyperliquid")

except ImportError:
    try:
        # Fallback: Try importing from src module
        from src import nice_funcs_hyperliquid as n
        from eth_account import Account

        def _get_account():
            key = os.getenv("HYPER_LIQUID_ETH_PRIVATE_KEY", "")
            clean_key = key.strip().replace('"', '').replace("'", "")
            return Account.from_key(clean_key)

        EXCHANGE_CONNECTED = True
        print("✅ HyperLiquid functions loaded from src.nice_funcs_hyperliquid")

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

# (keeping your existing functions as-is: get_account_data, get_positions_data,
# save_balance_history, load_trades, save_trade, add_console_log, etc.)
# ...

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

    # Save state
    state = load_agent_state()
    state["running"] = True
    state["last_started"] = datetime.now().isoformat()
    state["total_cycles"] = state.get("total_cycles", 0) + 1
    save_agent_state(state)

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


@app.route('/api/agent-status')
def get_agent_status():
    """Return current agent status and metadata."""
    try:
        state = load_agent_state()
        status = {
            "agent_running": agent_running,
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
    global agent_running, stop_agent_flag, shutdown_in_progress

    if shutdown_in_progress:
        return
    shutdown_in_progress = True

    print("\n\n" + "=" * 60)
    print("🛑 SHUTDOWN SIGNAL RECEIVED")
    print("=" * 60)

    if agent_running:
        print("⏹️  Stopping trading agent...")
        stop_agent_flag = True
        agent_running = False

        if agent_thread and agent_thread.is_alive():
            print("   Waiting for agent thread to finish...")
            agent_thread.join(timeout=5)

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

    try:
        add_console_log("Dashboard server shutting down", "info")
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
# STARTUP
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"""
{'=' * 60}
Marco's AI Trading Dashboard
{'=' * 60}
Dashboard URL: http://0.0.0.0:{port}
Local URL: http://localhost:{port}
Exchange: HyperLiquid
Status: {'Connected ✅' if EXCHANGE_CONNECTED else 'Demo Mode ⚠️'}
Agent: {'Running 🟢' if agent_running else 'Stopped 🔴'}
{'=' * 60}
Press Ctrl+C to shutdown gracefully
Port {port} will be released immediately on exit
""")

    add_console_log("Dashboard server started", "info")

    if not EXCHANGE_CONNECTED:
        add_console_log("Running in DEMO mode - HyperLiquid not connected", "warning")

    try:
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
