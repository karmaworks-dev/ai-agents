// Trading Dashboard Frontend - Updated for Agent

let updateInterval;
let portfolioChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dashboard initializing...');

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
            updateAgentBadge(agentStatus.running, agentStatus.executing);

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
    const pauseBtn = document.getElementById('pause-btn');

    if (isExecuting) {
        badge.textContent = 'RUNNING';
        badge.className = 'agent-badge running';
        runBtn.style.display = 'none';
        pauseBtn.style.display = 'inline-flex';
    } else if (isRunning) {
        badge.textContent = 'stand by';
        badge.className = 'agent-badge running';
        runBtn.style.display = 'none';
        pauseBtn.style.display = 'inline-flex';
    } else {
        badge.textContent = 'ready';
        badge.className = 'agent-badge ready';
        runBtn.style.display = 'inline-flex';
        pauseBtn.style.display = 'none';
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
        updateAgentBadge(data.running, false);  // Not executing on initial load

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
// THEME TOGGLE - REMOVED (Dark mode only)
// ============================================================================

// ============================================================================
// SETTINGS MODAL
// ============================================================================

// Global state for settings
let availableTokens = {};
let selectedTokens = [];
let availableProviders = [];
let availableModels = {};
let swarmModels = [];

function openSettings() {
    document.getElementById('settings-modal').classList.add('show');
    loadSettings();
}

function closeSettings(event) {
    if (!event || event.target.id === 'settings-modal' || event.target.classList.contains('modal-close')) {
        document.getElementById('settings-modal').classList.remove('show');
    }
}

// Tab switching
function switchSettingsTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update tab content
    document.querySelectorAll('.settings-tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });
}

// Load all settings from API
async function loadSettings() {
    try {
        // Load settings, tokens, and models in parallel
        const [settingsRes, tokensRes, modelsRes] = await Promise.all([
            fetch('/api/settings'),
            fetch('/api/tokens'),
            fetch('/api/ai-models')
        ]);

        const settingsData = await settingsRes.json();
        const tokensData = await tokensRes.json();
        const modelsData = await modelsRes.json();

        // Store available data
        if (tokensData.success) {
            availableTokens = tokensData.categories;
            populateTokenCategories();
        }

        if (modelsData.success) {
            availableProviders = modelsData.providers;
            availableModels = modelsData.models;
            populateProviderDropdowns();
        }

        // Apply settings
        if (settingsData.success) {
            applySettings(settingsData.settings);
        }

    } catch (error) {
        console.error('Error loading settings:', error);
        showValidationMessage('Failed to load settings', 'error');
    }
}

// Apply settings to UI
function applySettings(settings) {
    // Chart settings
    document.getElementById('timeframe-select').value = settings.timeframe || '30m';
    document.getElementById('days-back-select').value = settings.days_back || 2;
    document.getElementById('cycle-time-input').value = settings.sleep_minutes || 30;

    // Mode settings
    const swarmMode = settings.swarm_mode || 'single';
    document.querySelector(`input[name="swarm-mode"][value="${swarmMode}"]`).checked = true;
    updateSwarmModelsVisibility();

    // Token settings
    selectedTokens = settings.monitored_tokens || ['ETH', 'BTC', 'SOL'];
    updateTokenSelection();

    // Main model settings
    if (settings.ai_provider) {
        document.getElementById('main-provider-select').value = settings.ai_provider;
        updateMainModelOptions();
    }
    if (settings.ai_model) {
        document.getElementById('main-model-select').value = settings.ai_model;
    }

    // Temperature and max tokens
    const tempValue = Math.round((settings.ai_temperature || 0.3) * 100);
    document.getElementById('main-temperature').value = tempValue;
    updateSliderValue('main-temperature', 'main-temp-value');

    document.getElementById('main-max-tokens').value = settings.ai_max_tokens || 2000;

    // Swarm models
    swarmModels = settings.swarm_models || [
        { provider: 'gemini', model: 'gemini-2.5-flash', temperature: 0.3, max_tokens: 2000 }
    ];
    renderSwarmModels();
}

// Populate token categories
function populateTokenCategories() {
    const categories = ['crypto', 'altcoins', 'memecoins'];

    categories.forEach(category => {
        const container = document.getElementById(`${category}-tokens`);
        const tokens = availableTokens[category] || [];

        container.innerHTML = tokens.map(token => `
            <div class="token-chip" data-symbol="${token.symbol}" onclick="toggleToken('${token.symbol}')">
                <span class="token-symbol">${token.symbol}</span>
            </div>
        `).join('');
    });
}

// Toggle category expand/collapse
function toggleCategory(category) {
    const tokensContainer = document.getElementById(`${category}-tokens`);
    tokensContainer.classList.toggle('collapsed');

    // Update arrow rotation
    const header = tokensContainer.previousElementSibling;
    const arrow = header.querySelector('.category-arrow');
    arrow.style.transform = tokensContainer.classList.contains('collapsed') ? 'rotate(-90deg)' : '';
}

// Toggle token selection
function toggleToken(symbol) {
    const index = selectedTokens.indexOf(symbol);
    if (index === -1) {
        selectedTokens.push(symbol);
    } else {
        selectedTokens.splice(index, 1);
    }
    updateTokenSelection();
}

// Remove token from selection
function removeToken(symbol) {
    const index = selectedTokens.indexOf(symbol);
    if (index !== -1) {
        selectedTokens.splice(index, 1);
        updateTokenSelection();
    }
}

// Update token selection UI
function updateTokenSelection() {
    // Update chips
    document.querySelectorAll('.token-chip').forEach(chip => {
        const symbol = chip.dataset.symbol;
        chip.classList.toggle('selected', selectedTokens.includes(symbol));
    });

    // Update category counts
    const categories = ['crypto', 'altcoins', 'memecoins'];
    categories.forEach(category => {
        const tokens = availableTokens[category] || [];
        const count = tokens.filter(t => selectedTokens.includes(t.symbol)).length;
        document.getElementById(`${category}-count`).textContent = count;
    });

    // Update selected tokens summary
    const summaryContainer = document.getElementById('selected-tokens-list');
    if (selectedTokens.length === 0) {
        summaryContainer.innerHTML = '<span style="color: var(--text-muted); font-size: 12px;">No tokens selected</span>';
    } else {
        summaryContainer.innerHTML = selectedTokens.map(symbol => `
            <div class="selected-token">
                ${symbol}
                <span class="remove-token" onclick="removeToken('${symbol}')">&times;</span>
            </div>
        `).join('');
    }
}

// Populate provider dropdowns
function populateProviderDropdowns() {
    const mainProviderSelect = document.getElementById('main-provider-select');

    mainProviderSelect.innerHTML = availableProviders.map(provider => {
        const displayName = getProviderDisplayName(provider);
        return `<option value="${provider}">${displayName}</option>`;
    }).join('');

    // Set default and update models
    updateMainModelOptions();
}

// Get display name for provider
function getProviderDisplayName(provider) {
    const names = {
        'anthropic': 'Anthropic (Claude)',
        'openai': 'OpenAI',
        'gemini': 'Google Gemini',
        'deepseek': 'DeepSeek',
        'xai': 'xAI (Grok)',
        'mistral': 'Mistral AI',
        'cohere': 'Cohere',
        'perplexity': 'Perplexity',
        'groq': 'Groq',
        'ollama': 'Ollama (Local)',
        'openrouter': 'OpenRouter'
    };
    return names[provider] || provider;
}

// Update main model dropdown based on provider
function updateMainModelOptions() {
    const provider = document.getElementById('main-provider-select').value;
    const modelSelect = document.getElementById('main-model-select');
    const models = availableModels[provider] || {};

    modelSelect.innerHTML = Object.entries(models).map(([modelId, description]) => {
        return `<option value="${modelId}">${description}</option>`;
    }).join('');
}

// Update slider value display
function updateSliderValue(sliderId, displayId) {
    const slider = document.getElementById(sliderId);
    const display = document.getElementById(displayId);
    display.textContent = (slider.value / 100).toFixed(1);
}

// Update swarm models section visibility
function updateSwarmModelsVisibility() {
    const swarmMode = document.querySelector('input[name="swarm-mode"]:checked').value;
    const swarmSection = document.getElementById('swarm-models-section');
    swarmSection.classList.toggle('active', swarmMode === 'swarm');
}

// Listen for mode changes
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[name="swarm-mode"]').forEach(radio => {
        radio.addEventListener('change', updateSwarmModelsVisibility);
    });
});

// Render swarm models
function renderSwarmModels() {
    const container = document.getElementById('swarm-models-list');

    container.innerHTML = swarmModels.map((model, index) => `
        <div class="swarm-model-card" data-index="${index}">
            <div class="swarm-model-header">
                <span class="swarm-model-number">Model ${index + 1}</span>
                ${swarmModels.length > 1 ? `
                    <button class="btn-remove-model" onclick="removeSwarmModel(${index})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                    </button>
                ` : ''}
            </div>
            <div class="setting-row">
                <div class="setting-group half">
                    <label>Provider</label>
                    <select class="setting-input swarm-provider" data-index="${index}" onchange="updateSwarmModelOptions(${index})">
                        ${availableProviders.map(p => `
                            <option value="${p}" ${p === model.provider ? 'selected' : ''}>${getProviderDisplayName(p)}</option>
                        `).join('')}
                    </select>
                </div>
                <div class="setting-group half">
                    <label>Model</label>
                    <select class="setting-input swarm-model" data-index="${index}">
                        ${Object.entries(availableModels[model.provider] || {}).map(([id, desc]) => `
                            <option value="${id}" ${id === model.model ? 'selected' : ''}>${desc}</option>
                        `).join('')}
                    </select>
                </div>
            </div>
            <div class="setting-row">
                <div class="setting-group half">
                    <label>Temperature</label>
                    <div class="slider-container">
                        <input type="range" class="setting-slider swarm-temp" data-index="${index}" min="0" max="100" value="${Math.round(model.temperature * 100)}" oninput="updateSwarmSliderValue(${index})" />
                        <span class="slider-value" id="swarm-temp-${index}">${model.temperature.toFixed(1)}</span>
                    </div>
                </div>
                <div class="setting-group half">
                    <label>Max Tokens</label>
                    <input type="number" class="setting-input swarm-max-tokens" data-index="${index}" min="100" max="100000" value="${model.max_tokens}" />
                </div>
            </div>
        </div>
    `).join('');

    // Update add button state
    const addBtn = document.getElementById('add-model-btn');
    addBtn.disabled = swarmModels.length >= 6;
}

// Update swarm model options
function updateSwarmModelOptions(index) {
    const providerSelect = document.querySelector(`.swarm-provider[data-index="${index}"]`);
    const modelSelect = document.querySelector(`.swarm-model[data-index="${index}"]`);
    const provider = providerSelect.value;
    const models = availableModels[provider] || {};

    modelSelect.innerHTML = Object.entries(models).map(([id, desc]) => `
        <option value="${id}">${desc}</option>
    `).join('');

    // Update swarm models array
    swarmModels[index].provider = provider;
    swarmModels[index].model = Object.keys(models)[0] || '';
}

// Update swarm slider value
function updateSwarmSliderValue(index) {
    const slider = document.querySelector(`.swarm-temp[data-index="${index}"]`);
    const display = document.getElementById(`swarm-temp-${index}`);
    display.textContent = (slider.value / 100).toFixed(1);
}

// Add new swarm model
function addSwarmModel() {
    if (swarmModels.length >= 6) return;

    swarmModels.push({
        provider: 'gemini',
        model: 'gemini-2.5-flash',
        temperature: 0.3,
        max_tokens: 2000
    });

    renderSwarmModels();
}

// Remove swarm model
function removeSwarmModel(index) {
    if (swarmModels.length <= 1) return;
    swarmModels.splice(index, 1);
    renderSwarmModels();
}

// Collect swarm models from UI
function collectSwarmModels() {
    const models = [];
    document.querySelectorAll('.swarm-model-card').forEach((card, index) => {
        const provider = card.querySelector('.swarm-provider').value;
        const model = card.querySelector('.swarm-model').value;
        const tempSlider = card.querySelector('.swarm-temp');
        const maxTokens = card.querySelector('.swarm-max-tokens').value;

        models.push({
            provider: provider,
            model: model,
            temperature: parseFloat((tempSlider.value / 100).toFixed(1)),
            max_tokens: parseInt(maxTokens)
        });
    });
    return models;
}

// Show validation message
function showValidationMessage(message, type) {
    const el = document.getElementById('settings-validation');
    el.textContent = message;
    el.className = `validation-message ${type}`;

    if (type === 'success') {
        setTimeout(() => {
            el.className = 'validation-message';
        }, 3000);
    }
}

// Save all settings
async function saveSettings() {
    // Validate
    if (selectedTokens.length === 0) {
        showValidationMessage('Please select at least one token', 'error');
        return;
    }

    const cycleTime = parseInt(document.getElementById('cycle-time-input').value);
    if (cycleTime < 1 || cycleTime > 1440) {
        showValidationMessage('Cycle time must be between 1 and 1440 minutes', 'error');
        return;
    }

    const maxTokens = parseInt(document.getElementById('main-max-tokens').value);
    if (maxTokens < 100 || maxTokens > 100000) {
        showValidationMessage('Max tokens must be between 100 and 100,000', 'error');
        return;
    }

    // Collect settings
    const settings = {
        // Chart settings
        timeframe: document.getElementById('timeframe-select').value,
        days_back: parseInt(document.getElementById('days-back-select').value),
        sleep_minutes: cycleTime,

        // Mode settings
        swarm_mode: document.querySelector('input[name="swarm-mode"]:checked').value,

        // Token settings
        monitored_tokens: selectedTokens,

        // Main AI model settings
        ai_provider: document.getElementById('main-provider-select').value,
        ai_model: document.getElementById('main-model-select').value,
        ai_temperature: parseFloat((document.getElementById('main-temperature').value / 100).toFixed(1)),
        ai_max_tokens: maxTokens,

        // Swarm models
        swarm_models: collectSwarmModels()
    };

    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        const data = await response.json();

        if (data.success) {
            showValidationMessage('Settings saved successfully', 'success');
            addConsoleMessage('Settings saved successfully', 'success');
            setTimeout(() => closeSettings(), 1500);
        } else {
            showValidationMessage(data.message || 'Failed to save settings', 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showValidationMessage('Failed to save settings', 'error');
    }
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

    // Extract balance values
    const values = history.map(h => h.balance);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min;

    if (range === 0) {
        container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px;">Balance: $${values[0].toFixed(2)} (No change)</div>`;
        return;
    }

    // SVG dimensions
    const width = 600;
    const height = 120;
    const padding = 10;

    // Calculate points for the line
    const points = values.map((val, i) => {
        const x = (i / (values.length - 1)) * (width - padding * 2) + padding;
        const y = height - padding - ((val - min) / range) * (height - padding * 2);
        return { x, y };
    });

    // Create smooth path using quadratic bezier curves
    let pathD = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
        const prev = points[i - 1];
        const curr = points[i];
        const cpx = (prev.x + curr.x) / 2;
        const cpy = (prev.y + curr.y) / 2;
        pathD += ` Q ${prev.x} ${prev.y} ${cpx} ${cpy}`;
    }
    pathD += ` L ${points[points.length - 1].x} ${points[points.length - 1].y}`;

    // Create area fill path (for gradient)
    let areaD = pathD + ` L ${width - padding} ${height} L ${padding} ${height} Z`;

    // Determine color based on trend
    const trend = values[values.length - 1] >= values[0];
    const lineColor = trend ? 'var(--accent-green)' : 'var(--accent-red)';
    const gradientId = trend ? 'gradient-green' : 'gradient-red';

    container.innerHTML = `
        <svg width="100%" height="120" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" style="display: block;">
            <defs>
                <linearGradient id="gradient-green" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color: rgba(0, 255, 136, 0.3); stop-opacity: 1" />
                    <stop offset="100%" style="stop-color: rgba(0, 255, 136, 0); stop-opacity: 0" />
                </linearGradient>
                <linearGradient id="gradient-red" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color: rgba(255, 71, 87, 0.3); stop-opacity: 1" />
                    <stop offset="100%" style="stop-color: rgba(255, 71, 87, 0); stop-opacity: 0" />
                </linearGradient>
            </defs>

            <!-- Gradient fill under line -->
            <path d="${areaD}" fill="url(#${gradientId})" opacity="0.5"/>

            <!-- Main line -->
            <path d="${pathD}"
                  fill="none"
                  stroke="${lineColor}"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  filter="drop-shadow(0 0 3px ${lineColor})"
                  opacity="0.9"/>

            <!-- End point indicator -->
            <circle cx="${points[points.length - 1].x}"
                    cy="${points[points.length - 1].y}"
                    r="3"
                    fill="${lineColor}"
                    filter="drop-shadow(0 0 4px ${lineColor})"/>
        </svg>
    `;
}

// ============================================================================
// MENU TOGGLE
// ============================================================================

function toggleMenu() {
    const menu = document.getElementById('dropdown-menu');
    menu.classList.toggle('show');
}

// Close menu when clicking outside
document.addEventListener('click', (event) => {
    const menu = document.getElementById('dropdown-menu');
    const menuButton = event.target.closest('.icon-btn[onclick*="toggleMenu"]');

    if (!menu.contains(event.target) && !menuButton) {
        menu.classList.remove('show');
    }
});

// ============================================================================
// TIMEZONE MODAL
// ============================================================================

function openTimezoneModal() {
    document.getElementById('timezone-modal').classList.add('show');
    // Load current timezone
    const savedTimezone = localStorage.getItem('preferred_timezone') || 'local';
    document.getElementById('timezone-select').value = savedTimezone;
}

function closeTimezoneModal(event) {
    if (!event || event.target.id === 'timezone-modal' || event.target.classList.contains('modal-close')) {
        document.getElementById('timezone-modal').classList.remove('show');
    }
}

function confirmTimezone() {
    const select = document.getElementById('timezone-select');
    const selectedZone = select.value;
    localStorage.setItem('preferred_timezone', selectedZone);
    updateTimestamp(); // Refresh timestamp immediately
    updateConsole(); // Refresh console with new timezone
    closeTimezoneModal();
}

// ============================================================================
// ACCOUNT MODAL
// ============================================================================

function openAccountModal() {
    const modal = document.getElementById('account-modal');
    modal.classList.add('show');

    // Load account data
    const username = sessionStorage.getItem('username') || 'User';
    const email = sessionStorage.getItem('email') || 'user@example.com';

    document.getElementById('account-username').textContent = username;
    document.getElementById('account-email').textContent = email;

    // Load current model
    const currentModel = localStorage.getItem('ai_model') || 'claude-3-haiku-20240307';
    const modelNames = {
        'claude-3-haiku-20240307': 'Claude 3 Haiku',
        'claude-3-sonnet-20240229': 'Claude 3 Sonnet',
        'claude-3-opus-20240229': 'Claude 3 Opus',
        'gpt-4': 'GPT-4',
        'deepseek-chat': 'DeepSeek',
        'groq': 'Groq'
    };
    document.getElementById('account-current-model').textContent = modelNames[currentModel] || currentModel;

    // Calculate all-time PnL from history
    fetch('/api/history')
        .then(response => response.json())
        .then(history => {
            if (history && history.length > 0) {
                const startBalance = history[0].balance;
                const currentBalance = history[history.length - 1].balance;
                const totalPnl = currentBalance - startBalance;

                const pnlEl = document.getElementById('account-total-pnl');
                pnlEl.textContent = `${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}`;
                pnlEl.className = `stat-value pnl ${totalPnl >= 0 ? 'positive' : 'negative'}`;
            }
        })
        .catch(error => {
            console.error('Error loading PnL:', error);
        });
}

function closeAccountModal(event) {
    if (!event || event.target.id === 'account-modal' || event.target.classList.contains('modal-close')) {
        document.getElementById('account-modal').classList.remove('show');
    }
}

console.log('✅ Dashboard ready');
