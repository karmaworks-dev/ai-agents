"""
Settings Manager for AI Trading Dashboard
==========================================
Handles user-configurable settings storage and retrieval
"""

import json
import os
from pathlib import Path
from datetime import datetime

# Settings file location
SETTINGS_FILE = Path(__file__).parent.parent / "data" / "user_settings.json"

# Hyperliquid available tokens (categorized)
HYPERLIQUID_TOKENS = {
    "crypto": [
        {"symbol": "BTC", "name": "Bitcoin"},
        {"symbol": "ETH", "name": "Ethereum"},
        {"symbol": "SOL", "name": "Solana"},
    ],
    "altcoins": [
        {"symbol": "LTC", "name": "Litecoin"},
        {"symbol": "AAVE", "name": "Aave"},
        {"symbol": "LINK", "name": "Chainlink"},
        {"symbol": "AVAX", "name": "Avalanche"},
        {"symbol": "MATIC", "name": "Polygon"},
        {"symbol": "ARB", "name": "Arbitrum"},
        {"symbol": "OP", "name": "Optimism"},
        {"symbol": "ATOM", "name": "Cosmos"},
        {"symbol": "DOT", "name": "Polkadot"},
        {"symbol": "UNI", "name": "Uniswap"},
        {"symbol": "CRV", "name": "Curve"},
        {"symbol": "MKR", "name": "Maker"},
        {"symbol": "SNX", "name": "Synthetix"},
        {"symbol": "COMP", "name": "Compound"},
        {"symbol": "SUSHI", "name": "SushiSwap"},
        {"symbol": "INJ", "name": "Injective"},
        {"symbol": "TIA", "name": "Celestia"},
        {"symbol": "SEI", "name": "Sei"},
        {"symbol": "SUI", "name": "Sui"},
        {"symbol": "APT", "name": "Aptos"},
        {"symbol": "NEAR", "name": "NEAR Protocol"},
        {"symbol": "FTM", "name": "Fantom"},
        {"symbol": "HYPE", "name": "Hyperliquid"},
        {"symbol": "DYDX", "name": "dYdX"},
        {"symbol": "GMX", "name": "GMX"},
        {"symbol": "BLUR", "name": "Blur"},
        {"symbol": "LDO", "name": "Lido"},
        {"symbol": "FXS", "name": "Frax Share"},
        {"symbol": "RPL", "name": "Rocket Pool"},
        {"symbol": "PENDLE", "name": "Pendle"},
        {"symbol": "STX", "name": "Stacks"},
        {"symbol": "RUNE", "name": "THORChain"},
        {"symbol": "ORDI", "name": "ORDI"},
        {"symbol": "W", "name": "Wormhole"},
        {"symbol": "JUP", "name": "Jupiter"},
        {"symbol": "PYTH", "name": "Pyth Network"},
        {"symbol": "JTO", "name": "Jito"},
        {"symbol": "WIF", "name": "dogwifhat"},
    ],
    "memecoins": [
        {"symbol": "DOGE", "name": "Dogecoin"},
        {"symbol": "SHIB", "name": "Shiba Inu"},
        {"symbol": "PEPE", "name": "Pepe"},
        {"symbol": "FARTCOIN", "name": "FartCoin"},
        {"symbol": "BONK", "name": "Bonk"},
        {"symbol": "FLOKI", "name": "Floki"},
        {"symbol": "MEME", "name": "Memecoin"},
        {"symbol": "WEN", "name": "Wen"},
        {"symbol": "MYRO", "name": "Myro"},
        {"symbol": "MEW", "name": "Cat in a dogs world"},
        {"symbol": "POPCAT", "name": "Popcat"},
        {"symbol": "GOAT", "name": "Goatseus Maximus"},
        {"symbol": "PNUT", "name": "Peanut the Squirrel"},
        {"symbol": "NEIRO", "name": "Neiro"},
        {"symbol": "TURBO", "name": "Turbo"},
        {"symbol": "BRETT", "name": "Brett"},
        {"symbol": "MOG", "name": "Mog Coin"},
        {"symbol": "GIGA", "name": "GigaChad"},
    ]
}

# Default settings
DEFAULT_SETTINGS = {
    # Chart settings
    "timeframe": "30m",           # Default: 30 minutes
    "days_back": 2,               # Default: 2 days
    "sleep_minutes": 30,          # Default: 30 minutes between cycles (cycle time)

    # Mode settings
    "swarm_mode": "single",       # Default: single (options: single, swarm)

    # Token settings
    "monitored_tokens": ["ETH", "BTC", "SOL"],  # Default tokens to monitor

    # Main AI Model settings (BYOK - Bring Your Own Key)
    "ai_provider": "gemini",      # Default: gemini (options: anthropic, openai, gemini, deepseek, xai, mistral, cohere, ollama)
    "ai_model": "gemini-2.5-flash",  # Default model API name
    "ai_temperature": 0.3,        # Default: 0.3 (0.0 = deterministic, 1.0 = creative)
    "ai_max_tokens": 2000,        # Default: 2000 tokens

    # Swarm AI Model settings (for multi-agent mode)
    "swarm_models": [
        # Each model has provider, model, temperature, max_tokens
        {"provider": "gemini", "model": "gemini-2.5-flash", "temperature": 0.3, "max_tokens": 2000},
    ],

    # Timestamp
    "last_updated": None
}


def load_settings():
    """Load user settings from file, or return defaults if file doesn't exist"""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged = DEFAULT_SETTINGS.copy()
                merged.update(settings)
                return merged
        else:
            # Create default settings file
            save_settings(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS.copy()
    except Exception as e:
        print(f"⚠️ Error loading settings: {e}")
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    """Save user settings to file"""
    try:
        # Ensure data directory exists
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Add timestamp
        settings["last_updated"] = datetime.now().isoformat()

        # Write to file
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)

        return True
    except Exception as e:
        print(f"❌ Error saving settings: {e}")
        return False


def update_setting(key, value):
    """Update a single setting"""
    try:
        settings = load_settings()
        settings[key] = value
        return save_settings(settings)
    except Exception as e:
        print(f"❌ Error updating setting {key}: {e}")
        return False


def validate_timeframe(timeframe):
    """Validate timeframe string"""
    valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    return timeframe in valid_timeframes


def get_available_models_for_provider(provider):
    """
    Get list of available models for a specific AI provider
    Based on AI Models Reference Guide (December 2025)
    Returns dict with model info: {model_api_name: description}
    """
    models = {
        'anthropic': {
            'claude-opus-4-5-20251101': 'Claude Opus 4.5 - Latest flagship (200K context)',
            'claude-sonnet-4-5-20250929': 'Claude Sonnet 4.5 - Best balance (200K context) ⚡ Recommended',
            'claude-haiku-4-5-20251001': 'Claude Haiku 4.5 - Fastest, lowest cost (200K context)',
            'claude-opus-4-20250514': 'Claude Opus 4 - Powerful reasoning (200K context)',
            'claude-sonnet-4-20250514': 'Claude Sonnet 4 - Fast, efficient (200K context)',
        },
        'openai': {
            'gpt-5.2': 'GPT-5.2 - Latest flagship (400K context)',
            'gpt-5': 'GPT-5 - Frontier model (400K context)',
            'gpt-5-mini': 'GPT-5 Mini - Smaller, faster (400K context)',
            'gpt-4.1': 'GPT-4.1 - Large context (1M context)',
            'gpt-4.1-mini': 'GPT-4.1 Mini - Efficient (1M context)',
            'o3': 'o3 - Reasoning model (200K context)',
            'o3-mini': 'o3-mini - Smaller reasoning (200K context)',
            'o4-mini': 'o4-mini - Latest reasoning (200K context)',
        },
        'gemini': {
            'gemini-3-pro': 'Gemini 3 Pro - Latest flagship (1M context)',
            'gemini-3-flash': 'Gemini 3 Flash - Fast, cost-effective (1M context)',
            'gemini-2.5-pro': 'Gemini 2.5 Pro - Powerful, stable (1M context)',
            'gemini-2.5-flash': 'Gemini 2.5 Flash - Fast variant (1M context) ⚡ Recommended',
            'gemini-2.5-flash-lite': 'Gemini 2.5 Flash-Lite - Ultra-efficient (1M context)',
            'gemini-2.0-flash': 'Gemini 2.0 Flash - Multimodal (1M context)',
            'gemini-1.5-flash': 'Gemini 1.5 Flash - Legacy fast (1M context)',
            'gemini-1.5-pro': 'Gemini 1.5 Pro - Legacy pro (1M context)',
        },
        'xai': {
            'grok-4-1-fast-reasoning': 'Grok 4.1 Thinking - Best overall (2M context)',
            'grok-4-1-fast-non-reasoning': 'Grok 4.1 Non-Thinking - Instant (2M context)',
            'grok-4-fast-reasoning': 'Grok 4 Reasoning - Tool calling (2M context)',
            'grok-4-fast-non-reasoning': 'Grok 4 Non-Reasoning - Fast (2M context)',
            'grok-4': 'Grok 4 - Standard (256K context)',
            'grok-code-fast-1': 'Grok Code Fast - Coding optimized (256K context)',
        },
        'deepseek': {
            'deepseek-thinking-v3.2-exp': 'DeepSeek V3.2 Thinking - Latest reasoning (128K)',
            'deepseek-non-thinking-v3.2-exp': 'DeepSeek V3.2 Non-Thinking - Fast (128K)',
            'deepseek-reasoner-v3.1': 'DeepSeek V3.1 Reasoner - Strong reasoning (128K)',
            'deepseek-chat-v3.1': 'DeepSeek V3.1 Chat - General chat (128K)',
            'deepseek-chat': 'DeepSeek V3 - General purpose (128K) ⚡ Recommended',
            'deepseek-reasoner': 'DeepSeek R1 - Open reasoning (128K)',
        },
        'mistral': {
            'mistral-large-latest': 'Mistral Large 3 - Flagship (256K context)',
            'ministral-14b-latest': 'Ministral 14B - Efficient (128K context)',
            'ministral-8b-latest': 'Ministral 8B - Small & fast (128K context)',
            'mistral-small-latest': 'Mistral Small - Cost-effective (128K context) ⚡ Recommended',
            'devstral-2': 'Devstral 2 - Coding 123B (256K context)',
        },
        'cohere': {
            'command-a': 'Command A - Latest flagship (256K context)',
            'command-r-plus': 'Command R+ - RAG optimized (128K context)',
            'command-r': 'Command R - Efficient RAG (128K context)',
            'command': 'Command - General purpose (128K context)',
        },
        'perplexity': {
            'sonar-pro': 'Sonar Pro - Web-grounded (128K context)',
            'sonar': 'Sonar - Search-optimized (128K context)',
            'sonar-reasoning': 'Sonar Reasoning - Deep research (128K context)',
        },
        'groq': {
            'mixtral-8x7b-32768': 'Mixtral 8x7B - Fast inference (32K context)',
            'llama-3.3-70b-versatile': 'Llama 3.3 70B - Versatile (128K context)',
            'llama-3.2-11b-vision-preview': 'Llama 3.2 11B Vision - Vision capable',
        },
        'ollama': {
            'llama3.2': 'Llama 3.2 - Meta\'s balanced model (local)',
            'deepseek-chat': 'DeepSeek Chat - Reasoning model (local)',
            'qwen/qwen3:8b': 'Qwen3 8B - Fast reasoning (local)',
            'mistral': 'Mistral - General purpose (local)',
        },
        'openrouter': {
            'google/gemini-2.5-flash': 'Gemini 2.5 Flash via OpenRouter',
            'qwen/qwen3-max': 'Qwen 3 Max - Powerful reasoning',
            'anthropic/claude-opus-4.1': 'Claude Opus 4.1 via OpenRouter',
            'openai/gpt-5-mini': 'GPT-5 Mini via OpenRouter',
        }
    }
    return models.get(provider, {})


def validate_ai_provider(provider):
    """Validate AI provider"""
    valid_providers = ['anthropic', 'openai', 'gemini', 'deepseek', 'xai', 'mistral', 'cohere', 'perplexity', 'groq', 'ollama', 'openrouter']
    return provider in valid_providers


def validate_ai_temperature(temperature):
    """Validate AI temperature (0.0 to 1.0)"""
    try:
        temp = float(temperature)
        return 0.0 <= temp <= 1.0
    except (ValueError, TypeError):
        return False


def validate_ai_max_tokens(max_tokens):
    """Validate AI max tokens (100 to 100000)"""
    try:
        tokens = int(max_tokens)
        return 100 <= tokens <= 100000
    except (ValueError, TypeError):
        return False


def get_hyperliquid_tokens():
    """Get all available Hyperliquid tokens organized by category"""
    return HYPERLIQUID_TOKENS


def get_all_token_symbols():
    """Get a flat list of all available token symbols"""
    symbols = []
    for category, tokens in HYPERLIQUID_TOKENS.items():
        symbols.extend([t["symbol"] for t in tokens])
    return symbols


def validate_tokens(tokens):
    """Validate that all tokens are valid Hyperliquid tokens"""
    if not isinstance(tokens, list):
        return False
    valid_symbols = get_all_token_symbols()
    return all(token in valid_symbols for token in tokens)


def validate_swarm_mode(mode):
    """Validate swarm mode"""
    return mode in ['single', 'swarm']


def validate_swarm_models(models):
    """Validate swarm models configuration"""
    if not isinstance(models, list):
        return False, "swarm_models must be a list"

    if len(models) < 1 or len(models) > 6:
        return False, "swarm_models must have 1-6 models"

    for i, model in enumerate(models):
        if not isinstance(model, dict):
            return False, f"Swarm model {i+1} must be an object"

        required_fields = ['provider', 'model', 'temperature', 'max_tokens']
        for field in required_fields:
            if field not in model:
                return False, f"Swarm model {i+1} missing field: {field}"

        if not validate_ai_provider(model['provider']):
            return False, f"Swarm model {i+1} has invalid provider: {model['provider']}"

        if not validate_ai_temperature(model['temperature']):
            return False, f"Swarm model {i+1} has invalid temperature"

        if not validate_ai_max_tokens(model['max_tokens']):
            return False, f"Swarm model {i+1} has invalid max_tokens"

    return True, None


def validate_settings(settings):
    """Validate settings dictionary"""
    errors = []

    # Validate timeframe
    if "timeframe" in settings and not validate_timeframe(settings["timeframe"]):
        errors.append(f"Invalid timeframe: {settings['timeframe']}")

    # Validate days_back (1-30 days)
    if "days_back" in settings:
        try:
            days = int(settings["days_back"])
            if days < 1 or days > 30:
                errors.append("days_back must be between 1 and 30")
        except (ValueError, TypeError):
            errors.append("days_back must be a number")

    # Validate sleep_minutes (1-1440 minutes = 1 day max)
    if "sleep_minutes" in settings:
        try:
            minutes = int(settings["sleep_minutes"])
            if minutes < 1 or minutes > 1440:
                errors.append("sleep_minutes must be between 1 and 1440")
        except (ValueError, TypeError):
            errors.append("sleep_minutes must be a number")

    # Validate swarm_mode
    if "swarm_mode" in settings and not validate_swarm_mode(settings["swarm_mode"]):
        errors.append(f"Invalid swarm mode: {settings['swarm_mode']}")

    # Validate monitored_tokens
    if "monitored_tokens" in settings:
        if not isinstance(settings["monitored_tokens"], list):
            errors.append("monitored_tokens must be a list")
        elif len(settings["monitored_tokens"]) == 0:
            errors.append("monitored_tokens must have at least one token")
        # Note: We allow any tokens now since users might have custom needs

    # Validate AI provider
    if "ai_provider" in settings and not validate_ai_provider(settings["ai_provider"]):
        errors.append(f"Invalid AI provider: {settings['ai_provider']}")

    # Validate AI temperature
    if "ai_temperature" in settings and not validate_ai_temperature(settings["ai_temperature"]):
        errors.append("ai_temperature must be between 0.0 and 1.0")

    # Validate AI max tokens
    if "ai_max_tokens" in settings and not validate_ai_max_tokens(settings["ai_max_tokens"]):
        errors.append("ai_max_tokens must be between 100 and 100000")

    # Validate swarm_models if present
    if "swarm_models" in settings:
        valid, error = validate_swarm_models(settings["swarm_models"])
        if not valid:
            errors.append(error)

    return len(errors) == 0, errors
