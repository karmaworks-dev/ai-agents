#!/usr/bin/env python3
"""
🌙 Trading Dashboard Backend — Works Seamlessly with trading_agent.py
---------------------------------------------------------------------
Features:
- Flask REST API for trading agent control and dashboard updates
- Threaded AI trading agent execution with persistent state
- JSON storage for trades, history, logs, and agent status
- Compatible with HyperLiquid / Aster / Solana exchanges
- Safe, production-ready threading and signal handling
"""

import os
import sys
import json
import time
import signal
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# =====================================================================
# INITIAL SETUP
# =====================================================================

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))
load_dotenv()

# Flask initialization
app = Flask(__name__,
            template_folder=str(BASE_DIR / "dashboard" / "templates"),
            static_folder=str(BASE_DIR / "dashboard" / "static"),
            static_url_path="/static")

CORS(app)

# Data storage paths
DATA_DIR = BASE_DIR / "src" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRADES_FILE = DATA_DIR / "trades.json"
HISTORY_FILE = DATA_DIR / "balance_history.json"
CONSOLE_FILE = DATA_DIR / "console_logs.json"
AGENT_STATE_FILE = DATA_DIR / "agent_state.json"

# =====================================================================
# AGENT CONTROL FLAGS
# =====================================================================
agent_thread = None
agent_running = False
stop_agent_flag = False
shutdown_in_progress = False
lock = threading.Lock()

# =====================================================================
# LOGGING UTILITIES
# =====================================================================
def add_console_log(message: str, level: str = "info"):
    """Append console message to log file."""
    try:
        if CONSOLE_FILE.exists():
            with open(CONSOLE_FILE, "r") as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "message": str(message),
            "level": level
        })
        logs = logs[-200:]  # keep recent logs only

        with open(CONSOLE_FILE, "w") as f:
            json.dump(logs, f, indent=2)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] {level.upper()}: {message}")
    except Exception as e:
        print(f"⚠️ Logging error: {e}")

def get_console_logs():
    try:
        if not CONSOLE_FILE.exists():
            return []
        with open(CONSOLE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

# =====================================================================
# AGENT STATE UTILITIES
# =====================================================================
def load_agent_state():
    """Load agent persistent state."""
    if not AGENT_STATE_FILE.exists():
        return {"running": False, "last_started": None, "last_stopped": None, "total_cycles": 0}
    try:
        with open(AGENT_STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"running": False, "last_started": None, "last_stopped": None, "total_cycles": 0}

def save_agent_state(state: dict):
    try:
        with open(AGENT_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        add_console_log(f"⚠️ Could not save agent state: {e}", "error")

# =====================================================================
# TRADES & HISTORY
# =====================================================================
def save_trade(trade_data: dict):
    try:
        if TRADES_FILE.exists():
            with open(TRADES_FILE, "r") as f:
                trades = json.load(f)
        else:
            trades = []
        trades.append(trade_data)
        trades = trades[-100:]
        with open(TRADES_FILE, "w") as f:
            json.dump(trades, f, indent=2)
    except Exception as e:
        add_console_log(f"Trade save error: {e}", "error")

def load_trades():
    try:
        if TRADES_FILE.exists():
            with open(TRADES_FILE, "r") as f:
                return json.load(f)[-50:]
        return []
    except Exception:
        return []

def save_balance_history(balance):
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        else:
            history = []
        history.append({
            "timestamp": datetime.now().isoformat(),
            "balance": float(balance)
        })
        history = history[-200:]
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        add_console_log(f"⚠️ Error saving balance history: {e}", "error")

# =====================================================================
# TRADING AGENT LOOP
# =====================================================================
def run_trading_agent():
    """Main background loop for the trading agent."""
    global agent_running, stop_agent_flag

    add_console_log("🚀 Trading agent loop started", "success")

    try:
        # Import TradingAgent dynamically (no circular imports)
        try:
            from src.agents.trading_agent import TradingAgent
        except ImportError:
            from trading_agent import TradingAgent

        agent = TradingAgent()

        cycles = 0
        while agent_running and not stop_agent_flag:
            cycles += 1
            add_console_log(f"🤖 Starting trading cycle #{cycles}", "info")

            try:
                agent.run_trading_cycle()
            except Exception as e:
                add_console_log(f"❌ Error in trading cycle: {e}", "error")
                time.sleep(30)
                continue

            # Update state
            state = load_agent_state()
            state["total_cycles"] = cycles
            save_agent_state(state)

            add_console_log("✅ Cycle complete. Sleeping before next run...", "success")

            # Wait N minutes (from trading_agent)
            try:
                from trading_agent import SLEEP_BETWEEN_RUNS_MINUTES
            except Exception:
                SLEEP_BETWEEN_RUNS_MINUTES = 60
            for _ in range(SLEEP_BETWEEN_RUNS_MINUTES):
                if stop_agent_flag:
                    break
                time.sleep(60)

    except Exception as e:
        add_console_log(f"❌ Fatal agent error: {e}", "error")

    finally:
        agent_running = False
        stop_agent_flag = False
        state = load_agent_state()
        state["running"] = False
        state["last_stopped"] = datetime.now().isoformat()
        save_agent_state(state)
        add_console_log("🛑 Trading agent stopped.", "warning")

# =====================================================================
# AGENT CONTROL FUNCTIONS
# =====================================================================
def start_agent():
    global agent_thread, agent_running, stop_agent_flag
    with lock:
        if agent_running:
            return {"status": "already_running", "message": "Agent already running"}

        agent_running = True
        stop_agent_flag = False
        state = load_agent_state()
        state["running"] = True
        state["last_started"] = datetime.now().isoformat()
        save_agent_state(state)

        agent_thread = threading.Thread(target=run_trading_agent, daemon=True)
        agent_thread.start()

        add_console_log("🟢 Trading agent started via /api/start", "success")
        return {"status": "started", "message": "Agent started successfully"}

def stop_agent():
    global stop_agent_flag, agent_running
    with lock:
        if not agent_running:
            return {"status": "not_running", "message": "Agent is not running"}

        stop_agent_flag = True
        add_console_log("⏹️ Stop signal sent to agent", "warning")

        # Wait briefly for clean exit
        for _ in range(10):
            if not agent_running:
                break
            time.sleep(1)

        agent_running = False
        state = load_agent_state()
        state["running"] = False
        state["last_stopped"] = datetime.now().isoformat()
        save_agent_state(state)

        return {"status": "stopped", "message": "Agent stopped"}

# =====================================================================
# API ROUTES
# =====================================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/start", methods=["POST"])
def api_start():
    result = start_agent()
    return jsonify(result)

@app.route("/api/stop", methods=["POST"])
def api_stop():
    result = stop_agent()
    return jsonify(result)

@app.route("/api/agent-status")
def api_agent_status():
    """Return current agent state and metrics."""
    state = load_agent_state()
    state["agent_running"] = agent_running
    state["stop_requested"] = stop_agent_flag
    state["timestamp"] = datetime.now().isoformat()
    return jsonify(state)

@app.route("/api/console")
def api_console():
    logs = get_console_logs()
    return jsonify(logs)

@app.route("/api/trades")
def api_trades():
    return jsonify(load_trades())

@app.route("/api/history")
def api_history():
    try:
        if not HISTORY_FILE.exists():
            return jsonify([])
        with open(HISTORY_FILE, "r") as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify([])

@app.route("/api/data")
def api_data():
    """Simplified placeholder — extend if exchange data available."""
    state = load_agent_state()
    data = {
        "account_balance": 100.0,
        "total_equity": 100.0,
        "pnl": 0.0,
        "status": "Running" if agent_running else "Idle",
        "exchange": "HyperLiquid",
        "agent_running": agent_running,
        "timestamp": datetime.now().isoformat(),
        "agent_state": state
    }
    return jsonify(data)

# =====================================================================
# CLEANUP
# =====================================================================
def handle_shutdown(*_):
    global shutdown_in_progress
    if shutdown_in_progress:
        return
    shutdown_in_progress = True
    add_console_log("🧹 Shutting down Flask app...", "warning")
    stop_agent()
    time.sleep(2)
    os._exit(0)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# =====================================================================
# ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    add_console_log("🌍 Starting Trading Dashboard Flask server...", "info")
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
