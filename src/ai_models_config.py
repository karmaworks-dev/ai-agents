"""
AI Model Configuration
Comprehensive list of available models from all providers
"""

# ============================================================================
# GOOGLE GEMINI MODELS
# ============================================================================
GEMINI_MODELS = {
    # ⭐ Best for Trading (Fast & Effective)
    "gemini-2.5-flash": "Ultra-fast Gemini 2.5 (BEST for trading - low latency)",
    "gemini-2.5-pro": "Gemini 2.5 Pro with stronger reasoning (RECOMMENDED for complex analysis)",

    # Production Models
    "gemini-1.5-flash": "Fast Gemini 1.5 model",
    "gemini-1.5-flash-8b": "Lightweight Gemini 1.5 variant",
    "gemini-1.5-pro": "Gemini 1.5 Pro - balanced performance",

    # Experimental Models
    "gemini-2.0-flash-exp": "Experimental Gemini 2.0 Flash",
    "gemini-exp-1206": "Experimental preview model",
    "learnlm-1.5-pro-experimental": "Learning-focused experimental model",
}

# ============================================================================
# 🧠 ANTHROPIC CLAUDE MODELS
# ============================================================================
CLAUDE_MODELS = {
    # ⭐ Best for Trading
    "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet (BEST - fast + intelligent)",
    "claude-3-5-haiku-20241022": "Claude 3.5 Haiku (RECOMMENDED - fastest)",

    # Claude 3 Opus (Most Powerful)
    "claude-3-opus-20240229": "Claude 3 Opus - most capable",

    # Claude 3 Sonnet
    "claude-3-sonnet-20240229": "Claude 3 Sonnet - balanced",
    "claude-3-5-sonnet-20240620": "Claude 3.5 Sonnet (June 2024)",

    # Claude 3 Haiku (Fastest)
    "claude-3-haiku-20240307": "Claude 3 Haiku - fastest & cheapest",
}

# ============================================================================
# 🔥 OPENAI GPT MODELS
# ============================================================================
OPENAI_MODELS = {
    # ⭐ Best for Trading
    "gpt-4o": "GPT-4 Omni (BEST - fast multimodal)",
    "gpt-4o-mini": "GPT-4 Omni Mini (RECOMMENDED - fast & cheap)",

    # GPT-4 Turbo
    "gpt-4-turbo": "GPT-4 Turbo - latest",
    "gpt-4-turbo-2024-04-09": "GPT-4 Turbo (April 2024)",
    "gpt-4-turbo-preview": "GPT-4 Turbo Preview",
    "gpt-4-0125-preview": "GPT-4 Turbo (January 2025)",
    "gpt-4-1106-preview": "GPT-4 Turbo (November 2023)",

    # GPT-4
    "gpt-4": "GPT-4 - most capable",
    "gpt-4-0613": "GPT-4 (June 2023)",
    "gpt-4-32k": "GPT-4 32K context",
    "gpt-4-32k-0613": "GPT-4 32K (June 2023)",

    # GPT-3.5 Turbo
    "gpt-3.5-turbo": "GPT-3.5 Turbo - fast & cheap",
    "gpt-3.5-turbo-0125": "GPT-3.5 Turbo (January 2025)",
    "gpt-3.5-turbo-1106": "GPT-3.5 Turbo (November 2023)",
    "gpt-3.5-turbo-16k": "GPT-3.5 Turbo 16K context",

    # O1 Series (Reasoning Models)
    "o1-preview": "O1 Preview - advanced reasoning",
    "o1-mini": "O1 Mini - faster reasoning",
}

# ============================================================================
# 🚀 XAI GROK MODELS
# ============================================================================
XAI_GROK_MODELS = {
    # ⭐ Best for Trading
    "grok-beta": "Grok Beta (RECOMMENDED - latest version)",
    "grok-2-1212": "Grok 2 (December 2024)",

    # Available Models
    "grok-2-latest": "Grok 2 Latest",
    "grok-2": "Grok 2",
    "grok-vision-beta": "Grok Vision Beta - multimodal",
}

# ============================================================================
# ⚡ GROQ MODELS (Ultra-Fast Inference)
# ============================================================================
GROQ_MODELS = {
    # ⭐ Best for Trading (Fastest)
    "llama-3.3-70b-versatile": "Llama 3.3 70B (RECOMMENDED - balanced speed & quality)",
    "llama-3.1-8b-instant": "Llama 3.1 8B Instant (FASTEST)",

    # Llama Models
    "llama-3.3-70b-specdec": "Llama 3.3 70B Speculative",
    "llama-3.1-70b-versatile": "Llama 3.1 70B Versatile",
    "llama3-70b-8192": "Llama 3 70B",
    "llama3-8b-8192": "Llama 3 8B",

    # Mixtral Models
    "mixtral-8x7b-32768": "Mixtral 8x7B MoE",

    # Gemma Models
    "gemma2-9b-it": "Gemma 2 9B",
    "gemma-7b-it": "Gemma 7B",
}

# ============================================================================
# 🧮 DEEPSEEK MODELS (Reasoning)
# ============================================================================
DEEPSEEK_MODELS = {
    # ⭐ Best for Trading
    "deepseek-chat": "DeepSeek Chat (RECOMMENDED - balanced)",
    "deepseek-reasoner": "DeepSeek Reasoner (BEST for complex analysis)",

    # Available Models
    "deepseek-coder": "DeepSeek Coder - code-focused",
}

# ============================================================================
# 🏠 OLLAMA MODELS (Local)
# ============================================================================
OLLAMA_MODELS = {
    # Popular Local Models
    "llama3.3": "Llama 3.3 - latest",
    "llama3.2": "Llama 3.2",
    "llama3.1": "Llama 3.1",
    "mistral": "Mistral 7B",
    "mixtral": "Mixtral 8x7B",
    "qwen2.5": "Qwen 2.5",
    "deepseek-r1": "DeepSeek R1 - reasoning",
    "phi3": "Microsoft Phi-3",
    "gemma2": "Google Gemma 2",
}

# ============================================================================
# 🌐 OPENROUTER MODELS (200+ Models)
# ============================================================================
OPENROUTER_MODELS = {
    # Top Models for Trading
    "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet via OpenRouter",
    "openai/gpt-4o": "GPT-4 Omni via OpenRouter",
    "google/gemini-2.0-flash-exp:free": "Gemini 2.0 Flash FREE",
    "meta-llama/llama-3.3-70b-instruct": "Llama 3.3 70B",
    "deepseek/deepseek-chat": "DeepSeek Chat via OpenRouter",
    "x-ai/grok-beta": "Grok Beta via OpenRouter",
}

# ============================================================================
# 📊 RECOMMENDED MODELS FOR TRADING
# ============================================================================
TRADING_RECOMMENDED = {
    "fastest": {
        "model": "gemini-2.5-flash",
        "provider": "gemini",
        "description": "Ultra-fast for high-frequency analysis"
    },
    "balanced": {
        "model": "claude-3-5-haiku-20241022",
        "provider": "anthropic",
        "description": "Best speed/quality ratio"
    },
    "powerful": {
        "model": "gpt-4o",
        "provider": "openai",
        "description": "Most capable for complex market analysis"
    },
    "reasoning": {
        "model": "deepseek-reasoner",
        "provider": "deepseek",
        "description": "Best for strategy development"
    },
    "free": {
        "model": "google/gemini-2.0-flash-exp:free",
        "provider": "openrouter",
        "description": "Free tier with good performance"
    }
}

# ============================================================================
# 🎯 MODEL SELECTION HELPER
# ============================================================================
def get_all_models():
    """Get all available models across all providers"""
    return {
        "gemini": GEMINI_MODELS,
        "claude": CLAUDE_MODELS,
        "openai": OPENAI_MODELS,
        "xai": XAI_GROK_MODELS,
        "groq": GROQ_MODELS,
        "deepseek": DEEPSEEK_MODELS,
        "ollama": OLLAMA_MODELS,
        "openrouter": OPENROUTER_MODELS,
    }

def get_recommended_models():
    """Get recommended models for trading"""
    return TRADING_RECOMMENDED
