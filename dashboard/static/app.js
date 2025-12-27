// Trading Dashboard Frontend - Updated for Agent

let updateInterval;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dashboard initializing...');
    addConsoleMessage('🌐 Dashboard initialized');
    updateDashboard();
    updateInterval = setInterval(updateDashboard, 10000); // Update every 10 seconds
    
    // Update console logs separately
    setInterval(updateConsole, 5000); // Update console every 5 seconds
});

// Main update function
async function updateDashboard() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        if (!response.ok) throw new Error('API error');
        
        // Update metrics
        updateBalance(data.account_balance, data.total_equity);
        updatePnL(data.pnl);
        updateStatus(data.status, data.agent_running);
        updateExchange(data.exchange);
        updateTimestamp();
        updatePositions(data.positions);
        
        // Update agent badge
        updateAgentBadge(data.agent_running);
        
        // Fetch trades
        const tradesResponse = await fetch('/api/trades');
        const trades = await tradesResponse.json();
        updateTrades(trades);
        
    } catch (error) {
        console.error('❌ Dashboard update error:', error);
        setStatusOffline();
    }
}

// Update account balance
function updateBalance(available, equity) {
    document.getElementById('balance').textContent = `$${available.toFixed(2)}`;
    document.getElementById('equity').textContent = `$${equity.toFixed(2)}`;
}

// Update P&L
function updatePnL(pnl) {
    const pnlEl = document.getElementById('pnl');
    const pnlPctEl = document.getElementById('pnl-pct');
    
    const pnlClass = pnl >= 0 ? 'positive' : 'negative';
    pnlEl.className = `value pnl ${pnlClass}`;
    pnlEl.textContent = `${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`;
    
    const pnlPct = ((pnl / 10) * 100).toFixed(2); // Assuming $10 starting balance
    pnlPctEl.className = `sublabel ${pnlClass}`;
    pnlPctEl.textContent = `${pnl >= 0 ? '+' : ''}${pnlPct}%`;
}

// Update trading status
function updateStatus(status, isRunning) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = status;
    statusEl.className = 'sublabel ' + (isRunning ? 'running' : 'ready');
}

// Update exchange display
function updateExchange(exchange) {
    const exchangeEl = document.getElementById('exchange');
    exchangeEl.textContent = exchange || 'HyperLiquid';
}

// Update timestamp
function updateTimestamp() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { hour12: false });
    document.getElementById('timestamp').textContent = timeString;
}

// Update agent badge
function updateAgentBadge(isRunning) {
    const badge = document.getElementById('agent-badge');
    const runBtn = document.getElementById('run-btn');
    const stopBtn = document.getElementById('stop-btn');
    
    if (isRunning) {
        badge.textContent = 'Running';
        badge.className = 'agent-badge running';
        runBtn.style.display = 'none';
        stopBtn.style.display = 'inline-block';
    } else {
        badge.textContent = 'Ready';
        badge.className = 'agent-badge ready';
        runBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
    }
}

// Update positions display
function updatePositions(positions) {
    const container = document.getElementById('positions');
    const badge = document.getElementById('position-count');
    
    badge.textContent = positions.length;
    
    if (!positions || positions.length === 0) {
        container.innerHTML = '<div class="empty-state">No open positions</div>';
        return;
    }
    
    container.innerHTML = positions.map(pos => `
        <div class="position">
            <div class="position-item">
                <span class="position-label">Symbol</span>
                <span class="position-value">${pos.symbol}</span>
            </div>
            <div class="position-item">
                <span class="position-label">Side</span>
                <span class="position-value"><span class="side ${pos.side.toLowerCase()}">${pos.side}</span></span>
            </div>
            <div class="position-item">
                <span class="position-label">Size</span>
                <span class="position-value">${Math.abs(pos.size).toFixed(4)}</span>
            </div>
            <div class="position-item">
                <span class="position-label">Entry</span>
                <span class="position-value">$${pos.entry_price.toFixed(2)}</span>
            </div>
            <div class="position-item">
                <span class="position-label">P&L</span>
                <span class="position-value pnl ${pos.pnl_percent >= 0 ? 'positive' : 'negative'}">
                    ${pos.pnl_percent >= 0 ? '+' : ''}${pos.pnl_percent.toFixed(2)}%
                </span>
            </div>
        </div>
    `).join('');
}

// Update trades history
function updateTrades(trades) {
    const container = document.getElementById('trades');
    
    if (!trades || trades.length === 0) {
        container.innerHTML = '<div class="empty-state">No recent trades</div>';
        return;
    }
    
    container.innerHTML = trades.slice(0, 10).map(trade => {
        const timestamp = new Date(trade.timestamp).toLocaleString();
        const pnl = trade.pnl || 0;
        const pnlClass = pnl >= 0 ? 'positive' : 'negative';
        
        return `
            <div class="trade">
                <div class="trade-item">
                    <span class="trade-label">Time</span>
                    <span class="trade-value">${timestamp}</span>
                </div>
                <div class="trade-item">
                    <span class="trade-label">Symbol</span>
                    <span class="trade-value">${trade.symbol}</span>
                </div>
                <div class="trade-item">
                    <span class="trade-label">Side</span>
                    <span class="trade-value"><span class="side ${trade.side ? trade.side.toLowerCase() : 'long'}">${trade.side || 'LONG'}</span></span>
                </div>
                <div class="trade-item">
                    <span class="trade-label">Price</span>
                    <span class="trade-value">$${trade.price ? trade.price.toFixed(2) : '0.00'}</span>
                </div>
                <div class="trade-item">
                    <span class="trade-label">P&L</span>
                    <span class="trade-value pnl ${pnlClass}">${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}</span>
                </div>
            </div>
        `;
    }).join('');
}

// Update console logs
async function updateConsole() {
    try {
        const response = await fetch('/api/console');
        const logs = await response.json();
        
        const consoleEl = document.getElementById('console');
        
        if (logs.length === 0) {
            return;
        }
        
        // Keep only last 50 logs
        const recentLogs = logs.slice(-50);
        
        consoleEl.innerHTML = recentLogs.map(log => 
            `<div class="console-line">[${log.timestamp}] ${log.message}</div>`
        ).join('');
        
        // Auto-scroll to bottom
        consoleEl.scrollTop = consoleEl.scrollHeight;
        
    } catch (error) {
        console.error('Error updating console:', error);
    }
}

// Add console message locally
function addConsoleMessage(message) {
    const consoleEl = document.getElementById('console');
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    const line = document.createElement('div');
    line.className = 'console-line';
    line.textContent = `[${time}] ${message}`;
    consoleEl.appendChild(line);
    consoleEl.scrollTop = consoleEl.scrollHeight;
}

// Clear console
function clearConsole() {
    const consoleEl = document.getElementById('console');
    consoleEl.innerHTML = '<div class="console-line">🌐 Console cleared</div>';
}

// Run agent
async function runAgent() {
    try {
        addConsoleMessage('▶️ Starting trading agent...');
        const response = await fetch('/api/start', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'started') {
            addConsoleMessage('✅ Trading agent started successfully');
            updateDashboard(); // Immediate update
        } else {
            addConsoleMessage(`⚠️ ${data.message}`);
        }
    } catch (error) {
        addConsoleMessage(`❌ Error starting agent: ${error.message}`);
    }
}

// Stop agent
async function stopAgent() {
    try {
        addConsoleMessage('⏹️ Stopping trading agent...');
        const response = await fetch('/api/stop', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'stopped') {
            addConsoleMessage('✅ Trading agent stopped successfully');
            updateDashboard(); // Immediate update
        } else {
            addConsoleMessage(`⚠️ ${data.message}`);
        }
    } catch (error) {
        addConsoleMessage(`❌ Error stopping agent: ${error.message}`);
    }
}

// Set offline status
function setStatusOffline() {
    document.getElementById('status').className = 'sublabel offline';
    document.getElementById('status').textContent = 'Offline';
    document.getElementById('agent-badge').textContent = 'Disconnected';
    document.getElementById('agent-badge').className = 'agent-badge offline';
}

// Auto-update cleanup
window.addEventListener('beforeunload', () => {
    clearInterval(updateInterval);
});

console.log('✅ Dashboard ready');
