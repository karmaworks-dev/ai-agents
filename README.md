# AI Trading Dashboard

An AI-powered cryptocurrency trading platform with multi-model support, swarm consensus, and automated trading on HyperLiquid.

> **Current Status:** Pre-Beta Launch

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [AI Models](#ai-models)
- [Tier System](#tier-system)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Disclaimer](#disclaimer)

---

## Overview

This trading dashboard connects AI agents to HyperLiquid exchange for automated cryptocurrency trading. It supports multiple AI providers and features a unique "Swarm Mode" where multiple AI models reach consensus before executing trades.

### What It Does

1. **Monitors tokens** - Tracks prices, volume, and market data
2. **Analyzes markets** - Uses AI to interpret charts and indicators
3. **Makes decisions** - Single AI or multi-AI swarm consensus
4. **Executes trades** - Automated buy/sell on HyperLiquid

---

## Features

### AI Trading Modes

| Mode | Description | Speed |
|------|-------------|-------|
| **Single Agent** | One AI model analyzes and decides | ~10 seconds |
| **Swarm Mode** | 6 AI models vote for consensus | ~45-60 seconds |

### Supported AI Providers

| Provider | Models | API Key Required |
|----------|--------|------------------|
| Ollama (Local) | llama3, mistral, deepseek-coder | No (free, local) |
| OllamaFreeAPI | 650+ models | No (free, cloud) |
| Google Gemini | gemini-2.5-flash, gemini-2.5-pro | Yes |
| Anthropic | claude-4-sonnet, claude-4-opus | Yes |
| OpenAI | gpt-4o, gpt-4-turbo | Yes |
| Groq | mixtral-8x7b, llama-3.1-70b | Yes |
| DeepSeek | deepseek-chat, deepseek-coder | Yes |
| xAI | grok-2, grok-3 | Yes |
| OpenRouter | 200+ models | Yes |

### Dashboard Features

- Real-time portfolio balance and PnL
- Position monitoring with live updates
- Trade history with AI reasoning
- Configurable trading cycles (5-60 minutes)
- Token selection from HyperLiquid listings
- BYOK (Bring Your Own Key) for AI providers
- Tier-based feature access

---

## Quick Start

### Prerequisites

- Python 3.10+
- HyperLiquid account with API access
- At least one AI provider API key (or use free Ollama)

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai-agents.git
cd ai-agents

# 2. Create environment
conda create -n tflow python=3.10
conda activate tflow

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. (Optional) Install local Ollama for free AI
bash scripts/setup_ollama.sh

# 6. Run the dashboard
python trading_app.py
```

Open your browser to: **http://localhost:5000**

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/your-username/ai-agents.git
cd ai-agents
```

### Step 2: Create Python Environment

Using Conda (recommended):
```bash
conda create -n tflow python=3.10
conda activate tflow
```

Using venv:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# Required for trading
HYPER_LIQUID_ETH_PRIVATE_KEY=your_hyperliquid_private_key

# AI Providers (at least one required)
GEMINI_KEY=your_gemini_key
ANTHROPIC_KEY=your_anthropic_key
OPENAI_KEY=your_openai_key

# Optional providers
GROQ_API_KEY=your_groq_key
DEEPSEEK_KEY=your_deepseek_key
XAI_KEY=your_xai_key
OPENROUTER_API_KEY=your_openrouter_key
```

### Step 5: (Optional) Set Up Local Ollama

For free, unlimited, private AI:

```bash
bash scripts/setup_ollama.sh
```

This installs Ollama and pulls recommended models:
- `deepseek-coder:6.7b` - STEM/math specialist
- `llama3.2` - General purpose
- `mistral` - Fast general purpose

---

## Configuration

### Dashboard Settings

Access settings via the gear icon in the dashboard.

| Setting | Description | Default |
|---------|-------------|---------|
| Trading Mode | Single or Swarm | Single |
| Cycle Time | Minutes between analyses | 15 |
| Timeframe | Chart timeframe | 1H |
| Days Back | Historical data range | 7 |
| AI Provider | Which AI to use | Gemini |
| Temperature | AI creativity (0-1) | 0.3 |
| Max Tokens | Response length limit | 2000 |

### Token Selection

Select tokens to monitor from HyperLiquid's available markets:
- **Crypto**: BTC, ETH, SOL, etc.
- **Altcoins**: AVAX, LINK, DOGE, etc.
- **Memecoins**: PEPE, WIF, BONK, etc.

### Swarm Mode Configuration

When enabled, configure up to 6 AI models:

```
Model 1: Gemini 2.5 Flash (fast analysis)
Model 2: Claude 4 Sonnet (reasoning)
Model 3: GPT-4o (general)
Model 4: Grok-2 (real-time data)
Model 5: DeepSeek Chat (cost-effective)
Model 6: Mixtral 8x7B (balanced)
```

Trades execute only when majority (4+) agree.

---

## AI Models

### Free Options

#### Ollama (Local)
Run AI models locally for free with no rate limits:

```bash
# Install Ollama
bash scripts/setup_ollama.sh

# Or manually
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull deepseek-coder:6.7b
```

#### OllamaFreeAPI (Cloud)
Free cloud access to 650+ models:
- 100 requests/hour limit
- No API key required
- Includes DeepSeek, Llama, Mistral

### Paid Options

| Provider | Best For | Cost |
|----------|----------|------|
| Gemini | Free tier available | Free/$0.001 |
| Groq | Fast inference | ~$0.05/1M tokens |
| DeepSeek | Cost-effective | ~$0.14/1M tokens |
| Anthropic | Complex reasoning | ~$3/1M tokens |
| OpenAI | General purpose | ~$2.50/1M tokens |
| xAI | Real-time info | ~$2/1M tokens |

---

## Tier System

### Available Tiers

| Feature | Based (Free) | Trader ($5/mo) | Pro ($20/mo) |
|---------|--------------|----------------|--------------|
| Max Tokens | 5 | 10 | Unlimited |
| Cycle Time | 5+ min | 5+ min | Any |
| AI Mode | Single only | Single only | Swarm |
| BYOK | No | Yes | Yes |
| Providers | Ollama only | All | All |
| Swarm Models | - | - | Up to 6 |

### Admin Testing

For testing, admin users can switch between all tiers:
- KW-Trader
- admin
- moondev

---

## Architecture

### Project Structure

```
ai-agents/
├── trading_app.py          # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from .env.example)
│
├── dashboard/
│   ├── templates/
│   │   └── index.html      # Main dashboard HTML
│   └── static/
│       ├── app.js          # Frontend JavaScript
│       └── style.css       # Dashboard styles
│
├── src/
│   ├── agents/             # 48+ trading agents
│   │   ├── trading_agent.py
│   │   ├── risk_agent.py
│   │   ├── swarm_agent.py
│   │   └── ...
│   │
│   ├── models/             # AI model integrations
│   │   ├── model_factory.py
│   │   ├── ollama_model.py
│   │   ├── ollamafreeapi_model.py
│   │   ├── gemini_model.py
│   │   └── ...
│   │
│   ├── utils/
│   │   ├── settings_manager.py
│   │   ├── secrets_manager.py
│   │   └── tier_manager.py
│   │
│   ├── config.py           # Global configuration
│   ├── nice_funcs.py       # Trading utilities
│   └── nice_funcs_hl.py    # HyperLiquid utilities
│
└── scripts/
    └── setup_ollama.sh     # Ollama installation script
```

### Data Flow

```
User Settings → Trading Agent → AI Analysis → Decision → HyperLiquid API
                     ↓
              Market Data (OHLCV)
                     ↓
              Technical Indicators
                     ↓
              AI Prompt Generation
                     ↓
              Model Response (BUY/SELL/HOLD)
                     ↓
              Trade Execution
```

---

## API Reference

### Dashboard Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/data` | GET | Portfolio and positions |
| `/api/settings` | GET/POST | User settings |
| `/api/ai-models` | GET | Available AI models |
| `/api/tier` | GET/POST | Tier information |
| `/api/secrets` | GET | BYOK API key status |
| `/api/agent-status` | GET | Trading agent status |

### Trading Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/start-agent` | POST | Start trading agent |
| `/api/stop-agent` | POST | Stop trading agent |
| `/api/trades` | GET | Trade history |
| `/api/history` | GET | Balance history |

---

## Troubleshooting

### Common Issues

#### "No AI models available"
- Check your API keys in `.env`
- Verify at least one AI provider is configured
- Try using free Ollama: `bash scripts/setup_ollama.sh`

#### "HyperLiquid not connected"
- Verify `HYPER_LIQUID_ETH_PRIVATE_KEY` in `.env`
- Check your HyperLiquid account has trading enabled

#### "Module not found" errors
```bash
pip install -r requirements.txt
```

#### Ollama not responding
```bash
# Check if running
curl http://localhost:11434/api/tags

# Start if not
ollama serve
```

### Logs

Check console output for detailed logs:
- Green: Success
- Yellow: Warning
- Red: Error

---

## Disclaimer

**This is experimental software. Trading involves substantial risk of loss.**

- No guarantee of profitability
- Past performance does not indicate future results
- You are responsible for your own trading decisions
- Only trade with funds you can afford to lose
- This is NOT financial advice

**There is no token associated with this project.** Any token claiming affiliation is a scam.

---

## Links

- Discord: [discord.gg/8UPuVZ53bh](https://discord.gg/8UPuVZ53bh)
- YouTube Updates: [Moon Dev Playlist](https://www.youtube.com/playlist?list=PLXrNVMjRZUJg4M4uz52iGd1LhXXGVbIFz)
- Website: [moondev.com](https://moondev.com)

---

## License

Open source for educational purposes. Use at your own risk.

*Built by Moon Dev*
