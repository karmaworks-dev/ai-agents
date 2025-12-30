// Trading Dashboard Frontend - Updated for Agent

let updateInterval;
let portfolioChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dashboard initializing...');

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
        document.getElementById('theme-icon').textContent = '🌙';
    }

    // Load saved timezone preference
    const savedTimezone = localStorage.getItem('preferred_timezone') || 'local';
    const timezoneSelect = document.getElementById('timezone-select');
    if (timezoneSelect) {
        timezoneSelect.value = savedTimezone;
    }

    // Load settings
    loadSettings();

    // Load agent state first
    loadAgentState();

    // Initial updates
    updateDashboard();
    updateConsole();
    updateTimestamp(); // Initialize timestamp with saved timezone

    // Set up intervals
    updateInterval = setInterval(updateDashboard, 10000); // Changed to 10000 (10s)
    setInterval(updateConsole, 10000);
    setInterval(updateTimestamp, 1000); // Update timestamp every second

    console.log('✅ Dashboard ready - auto-refresh enabled');
});


// Main update function
// Smart update function - pauses heavy queries during agent execution
async function updateDashboard() {
    try {
        // First check if agent is actively executing
        const statusResponse = await fetch('/api/agent-status');
        const agentStatus = await statusResponse.json();
        
        // If agent is actively executing, do lightweight update
        if (agentStatus.executing) {
            console.log('[Dashboard] Agent executing - lightweight update only');
            
            // Only update timestamp and agent badge (no API calls)
            updateTimestamp();
            updateAgentBadge(agentStatus.running);
            
            return; // Skip heavy updates
        }
        
        // Agent is idle - do full update
        const response = await fetch('/api/data');

        if (!response.ok) {
            console.error('API returned error:', response.status);

            // Handle authentication errors
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }

            setStatusOffline();
            return;
        }
        
        const data = await response.json();
        
        console.log('[Dashboard] Full update at', new Date().toLocaleTimeString());
        
        // Update all metrics
        updateBalance(data.account_balance, data.total_equity);
        updatePnL(data.pnl);
        updateStatus(data.status, data.agent_running);
        updateExchange(data.exchange);
        updateTimestamp();
        updatePositions(data.positions);
        updateAgentBadge(data.agent_running, agentStatus.executing); // Pass execution state
        
        // Fetch trades
        const tradesResponse = await fetch('/api/trades');
        const trades = await tradesResponse.json();
        updateTrades(trades);

        // Update portfolio chart
        updatePortfolioChart();

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

// Update timezone preference
function updateTimezone() {
    const select = document.getElementById('timezone-select');
    const selectedZone = select.value;
    localStorage.setItem('preferred_timezone', selectedZone);
    updateTimestamp(); // Refresh timestamp immediately
    updateConsole(); // Refresh console with new timezone
}

// Update timestamp with timezone support
function updateTimestamp() {
    const now = new Date();
    const timezone = localStorage.getItem('preferred_timezone') || 'local';

    let timeString;
    if (timezone === 'local') {
        timeString = now.toLocaleTimeString('en-US', { hour12: false });
    } else if (timezone === 'UTC') {
        timeString = now.toLocaleTimeString('en-US', {
            hour12: false,
            timeZone: 'UTC'
        });
    } else {
        timeString = now.toLocaleTimeString('en-US', {
            hour12: false,
            timeZone: timezone
        });
    }

    document.getElementById('timestamp').textContent = timeString;
}

// Update agent badge with execution state (no API calls - uses passed data)
function updateAgentBadge(isRunning, isExecuting = false) {
    const badge = document.getElementById('agent-badge');
    const runBtn = document.getElementById('run-btn');
    const stopBtn = document.getElementById('stop-btn');
    
    if (isExecuting) {
        badge.textContent = 'Analyzing';
        badge.className = 'agent-badge running';
        runBtn.style.display = 'none';
        stopBtn.style.display = 'inline-block';
    } else if (isRunning) {
        badge.textContent = 'Waiting';
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

// Update positions display with 7 fields

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
                <span class="position-label">Position Value</span>
                <span class="position-value">$${pos.position_value ? pos.position_value.toFixed(2) : '0.00'}</span>
            </div>
            <div class="position-item">
                <span class="position-label">Entry Price</span>
                <span class="position-value">$${pos.entry_price.toFixed(2)}</span>
            </div>
            <div class="position-item">
                <span class="position-label">Mark Price</span>
                <span class="position-value">$${pos.mark_price ? pos.mark_price.toFixed(2) : pos.entry_price.toFixed(2)}</span>
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

// Update trades history (simplified plain text)

function updateTrades(trades) {
    const container = document.getElementById('trades');
    
    if (!trades || trades.length === 0) {
        container.innerHTML = '<div class="empty-state">No recent trades</div>';
        return;
    }
    
    // Show last 10 trades as simple text lines
    container.innerHTML = trades.slice(0, 10).map(trade => {
        const time = new Date(trade.timestamp).toLocaleTimeString('en-US', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit'
        });
        const pnl = trade.pnl || 0;
        const pnlStr = pnl >= 0 ? `+$${pnl.toFixed(2)}` : `-$${Math.abs(pnl).toFixed(2)}`;
        const pnlClass = pnl >= 0 ? 'positive' : 'negative';
        const side = trade.side || 'LONG';
        
        return `
            <div class="trade-line">
                <span class="trade-time">${time}</span>
                <span class="trade-symbol">${trade.symbol}</span>
                <span class="side ${side.toLowerCase()}">${side}</span>
                <span class="trade-pnl pnl ${pnlClass}">${pnlStr}</span>
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
            consoleEl.innerHTML = '<div class="console-line info">No activity yet</div>';
            return;
        }
        
        // Keep last 50 logs and REVERSE (newest first)
        const recentLogs = logs.slice(-50).reverse();
        
        // Get selected timezone
        const timezone = localStorage.getItem('preferred_timezone') || 'local';
        
        // Render with level classes and selective emojis
        consoleEl.innerHTML = recentLogs.map(log => {
            const emoji = getLogEmoji(log);
            const levelClass = log.level || 'info';
            
            // Convert timestamp to selected timezone
            const displayTime = convertTimestamp(log.timestamp, timezone);
            
            return `<div class="console-line ${levelClass}">${emoji}[${displayTime}] ${log.message}</div>`;
        }).join('');
        
    } catch (error) {
        console.error('Error updating console:', error);
    }
}

// Helper function for selective emoji usage
function getLogEmoji(log) {
    const msg = log.message.toLowerCase();
    const level = log.level || 'info';
    
    // Only add emoji for important events
    if (level === 'success' && msg.includes('started')) return '▶️ ';
    if (level === 'info' && msg.includes('stopped')) return '⏹️ ';
    if (level === 'trade') {
        // Emoji already in message from backend
        if (msg.includes('📈') || msg.includes('📉')) return '';
    }
    if (level === 'error') return '❌ ';
    
    return ''; // No emoji for most messages
}

// Convert timestamp to selected timezone
function convertTimestamp(timestamp, timezone) {
    // Backend sends HH:MM:SS in UTC
    // We need to parse it and convert to selected timezone
    
    try {
        // Get today's date and combine with the time
        const now = new Date();
        const [hours, minutes, seconds] = timestamp.split(':').map(Number);
        
        // Create UTC date object
        const utcDate = new Date(Date.UTC(
            now.getUTCFullYear(),
            now.getUTCMonth(),
            now.getUTCDate(),
            hours,
            minutes,
            seconds || 0
        ));
        
        if (timezone === 'local') {
            // Convert to user's local timezone
            return utcDate.toLocaleTimeString('en-US', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } else if (timezone === 'UTC') {
            // Keep as UTC
            return timestamp;
        } else {
            // Convert to specific timezone
            return utcDate.toLocaleTimeString('en-US', {
                hour12: false,
                timeZone: timezone,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    } catch (error) {
        // If conversion fails, return original
        return timestamp;
    }
}

// Load agent state on page load
async function loadAgentState() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        console.log('Agent state loaded:', data);
        
        // Update UI based on persisted state
        updateAgentBadge(data.running);
        
        // Log last action info
        if (data.last_started) {
            const lastStart = new Date(data.last_started).toLocaleTimeString();
            console.log(`Last agent start: ${lastStart}`);
        }
        if (data.last_stopped) {
            const lastStop = new Date(data.last_stopped).toLocaleTimeString();
            console.log(`Last agent stop: ${lastStop}`);
        }
        
    } catch (error) {
        console.error('Error loading agent state:', error);
    }
}

// Add console message locally (prepends to top)
function addConsoleMessage(message, level = 'info') {
    const consoleEl = document.getElementById('console');
    const time = new Date().toLocaleTimeString('en-US', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    const line = document.createElement('div');
    line.className = `console-line ${level}`;
    line.textContent = `[${time}] ${message}`;
    
    // Prepend to top (newest first)
    consoleEl.insertBefore(line, consoleEl.firstChild);
    
    // Keep only last 50 messages
    while (consoleEl.children.length > 50) {
        consoleEl.removeChild(consoleEl.lastChild);
    }
}

// Clear console
function clearConsole() {
    const consoleEl = document.getElementById('console');
    consoleEl.innerHTML = '<div class="console-line info">Console cleared</div>';
}

// Run agent
async function runAgent() {
    try {
        addConsoleMessage('Starting trading agent...', 'info');
        const response = await fetch('/api/start', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'started') {
            addConsoleMessage('Trading agent started successfully', 'success');
            updateDashboard(); // Immediate update
        } else if (data.status === 'already_running') {
            addConsoleMessage('Agent is already running', 'warning');
        } else {
            addConsoleMessage(data.message, 'warning');
        }
    } catch (error) {
        addConsoleMessage(`Error starting agent: ${error.message}`, 'error');
    }
}

// Stop agent
async function stopAgent() {
    try {
        addConsoleMessage('Stopping trading agent...', 'info');
        const response = await fetch('/api/stop', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'stopped') {
            addConsoleMessage('Trading agent stopped successfully', 'info');
            updateDashboard(); // Immediate update
        } else if (data.status === 'not_running') {
            addConsoleMessage('Agent is not running', 'warning');
        } else {
            addConsoleMessage(data.message, 'warning');
        }
    } catch (error) {
        addConsoleMessage(`Error stopping agent: ${error.message}`, 'error');
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

// ============================================================================
// THEME TOGGLE
// ============================================================================

function toggleTheme() {
    const body = document.body;
    const themeIcon = document.getElementById('theme-icon');

    if (body.classList.contains('light-mode')) {
        // Switch to dark mode
        body.classList.remove('light-mode');
        themeIcon.textContent = '☀️';
        localStorage.setItem('theme', 'dark');
    } else {
        // Switch to light mode
        body.classList.add('light-mode');
        themeIcon.textContent = '🌙';
        localStorage.setItem('theme', 'light');
    }
}

// ============================================================================
// SETTINGS MODAL
// ============================================================================

function openSettings() {
    document.getElementById('settings-modal').classList.add('show');
    loadSettings();
}

function closeSettings(event) {
    if (!event || event.target.id === 'settings-modal' || event.target.classList.contains('modal-close')) {
        document.getElementById('settings-modal').classList.remove('show');
    }
}

function loadSettings() {
    // Load settings from localStorage
    const exchange = localStorage.getItem('exchange') || 'HYPERLIQUID';
    const tokens = localStorage.getItem('tokens') || 'ETH, BTC, SOL, AAVE, LINK, LTC, FARTCOIN';
    const model = localStorage.getItem('ai_model') || 'claude-3-haiku-20240307';

    document.getElementById('exchange-select').value = exchange;
    document.getElementById('tokens-input').value = tokens;
    document.getElementById('model-select').value = model;
}

async function saveSettings() {
    const exchange = document.getElementById('exchange-select').value;
    const tokens = document.getElementById('tokens-input').value;
    const model = document.getElementById('model-select').value;

    // Save to localStorage
    localStorage.setItem('exchange', exchange);
    localStorage.setItem('tokens', tokens);
    localStorage.setItem('ai_model', model);

    // Send to backend API
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                exchange: exchange,
                tokens: tokens.split(',').map(t => t.trim()),
                ai_model: model
            })
        });

        const data = await response.json();
        addConsoleMessage('Settings saved successfully', 'success');
    } catch (error) {
        console.error('Error saving settings:', error);
        addConsoleMessage('Settings saved locally (backend update failed)', 'warning');
    }

    closeSettings();
}

// ============================================================================
// LOGOUT
// ============================================================================

async function logout() {
    try {
        const response = await fetch('/api/logout', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            // Redirect to login page
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Redirect anyway
        window.location.href = '/login';
    }
}

// ============================================================================
// PORTFOLIO CHART
// ============================================================================

async function updatePortfolioChart() {
    try {
        const response = await fetch('/api/history');
        const history = await response.json();

        if (!history || history.length === 0) {
            document.getElementById('portfolio-chart').innerHTML = 'No portfolio data yet';
            return;
        }

        // Calculate portfolio change
        const startBalance = history[0].balance;
        const currentBalance = history[history.length - 1].balance;
        const change = ((currentBalance - startBalance) / startBalance) * 100;

        const badge = document.getElementById('portfolio-change');
        badge.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
        badge.className = `badge ${change >= 0 ? 'positive' : 'negative'}`;

        // Render simple ASCII chart
        renderPortfolioChart(history);

    } catch (error) {
        console.error('Error updating portfolio chart:', error);
    }
}

function renderPortfolioChart(history) {
    const container = document.getElementById('portfolio-chart');

    // Simple sparkline visualization
    const values = history.map(h => h.balance);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min;

    if (range === 0) {
        container.innerHTML = `Balance: $${values[0].toFixed(2)} (No change)`;
        return;
    }

    // Create simple bars
    const bars = values.map(val => {
        const height = ((val - min) / range) * 100;
        return `<div style="height: ${height}%; background: var(--accent-green); width: ${100 / values.length}%; display: inline-block;"></div>`;
    }).join('');

    container.innerHTML = `
        <div style="width: 100%; height: 100%; display: flex; align-items: flex-end; gap: 2px;">
            ${bars}
        </div>
    `;
}

console.log('✅ Dashboard ready');
