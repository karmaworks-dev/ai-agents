"""
🌙 Moon Dev's Model Factory
Built with love by Moon Dev 🚀

This module manages all available AI models and provides a unified interface.
"""

import os
from typing import Dict, Optional, Type
from termcolor import cprint
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*args, **kwargs):
        return None
from pathlib import Path
from .base_model import BaseModel

# Try importing optional model adapters; set to None if not available
ClaudeModel = None
GroqModel = None
OpenAIModel = None
GeminiModel = None
DeepSeekModel = None
OllamaModel = None
OllamaFreeAPIModel = None
XAIModel = None
OpenRouterModel = None

try:
    from .claude_model import ClaudeModel
except Exception as e:
    cprint(f"⚠️ claude_model not available: {e}", "yellow")

try:
    from .groq_model import GroqModel
except Exception as e:
    cprint(f"⚠️ groq_model not available: {e}", "yellow")

try:
    from .openai_model import OpenAIModel
except Exception as e:
    cprint(f"⚠️ openai_model not available: {e}", "yellow")

try:
    from .gemini_model import GeminiModel
except Exception as e:
    cprint(f"⚠️ gemini_model not available: {e}", "yellow")

try:
    from .deepseek_model import DeepSeekModel
except Exception as e:
    cprint(f"⚠️ deepseek_model not available: {e}", "yellow")

try:
    from .ollama_model import OllamaModel
except Exception as e:
    cprint(f"⚠️ ollama_model not available: {e}", "yellow")

try:
    from .ollamafreeapi_model import OllamaFreeAPIModel
except Exception as e:
    cprint(f"⚠️ ollamafreeapi_model not available: {e}", "yellow")

try:
    from .xai_model import XAIModel
except Exception as e:
    cprint(f"⚠️ xai_model not available: {e}", "yellow")

try:
    from .openrouter_model import OpenRouterModel
except Exception as e:
    cprint(f"⚠️ openrouter_model not available: {e}", "yellow")
import random

class ModelFactory:
    """Factory for creating and managing AI models"""
    
    # Map model types to their implementations
    # Build the implementations mapping only with adapters that are actually imported
    MODEL_IMPLEMENTATIONS = {}
    if ClaudeModel is not None:
        MODEL_IMPLEMENTATIONS["claude"] = ClaudeModel
    if GroqModel is not None:
        MODEL_IMPLEMENTATIONS["groq"] = GroqModel
    if OpenAIModel is not None:
        MODEL_IMPLEMENTATIONS["openai"] = OpenAIModel
    if GeminiModel is not None:
        MODEL_IMPLEMENTATIONS["gemini"] = GeminiModel
    if DeepSeekModel is not None:
        MODEL_IMPLEMENTATIONS["deepseek"] = DeepSeekModel
    if OllamaModel is not None:
        MODEL_IMPLEMENTATIONS["ollama"] = OllamaModel
    if OllamaFreeAPIModel is not None:
        MODEL_IMPLEMENTATIONS["ollamafreeapi"] = OllamaFreeAPIModel
    if XAIModel is not None:
        MODEL_IMPLEMENTATIONS["xai"] = XAIModel
    if OpenRouterModel is not None:
        MODEL_IMPLEMENTATIONS["openrouter"] = OpenRouterModel
    
    # Default models for each type - OPTIMIZED FOR TRADING
    # Priority: Quantized models for memory efficiency where available
    DEFAULT_MODELS = {
        "claude": "claude-sonnet-4-5-20250929",      # Claude Sonnet 4.5 - balanced
        "groq": "llama-3.3-70b-versatile",           # Groq LLaMA 3.3 - FREE, fast
        "openai": "gpt-4.1-mini",                    # GPT-4.1 Mini - efficient
        "gemini": "gemini-2.5-flash",                # Gemini 2.5 Flash - FREE tier
        "deepseek": "deepseek-chat",                 # DeepSeek V3 - general purpose
        "ollama": "deepseek-v3.1:671b-q4_K_M",       # DeepSeek V3.1 Quantized - memory efficient
        "ollamafreeapi": "deepseek-v3.2",            # DeepSeek V3.2 - FREE, latest flagship
        "xai": "grok-4-1-fast-reasoning",            # xAI's Grok 4.1 - best overall
        "openrouter": "google/gemini-2.5-flash"      # OpenRouter - fast Gemini
    }
    
    def __init__(self):
        # Load environment variables (noop if python-dotenv not installed)
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / '.env'
        try:
            load_dotenv(dotenv_path=env_path)
        except Exception:
            pass

        self._models: Dict[str, BaseModel] = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all available models with detailed logging"""
        cprint("\n⚙️ Initializing AI Model Factory...", "cyan", attrs=["bold"])

        initialized_count = 0
        failed_models = []

        # Initialize API-based models (require API keys)
        for model_type, key_name in self._get_api_key_mapping().items():
            api_key = os.getenv(key_name)
            if api_key:
                try:
                    if model_type in self.MODEL_IMPLEMENTATIONS:
                        model_class = self.MODEL_IMPLEMENTATIONS[model_type]
                        model_instance = model_class(api_key)

                        if model_instance.is_available():
                            self._models[model_type] = model_instance
                            cprint(f"   ✅ {model_type}: {model_instance.model_name}", "green")
                            initialized_count += 1
                        else:
                            failed_models.append((model_type, "Model not available"))
                except Exception as e:
                    failed_models.append((model_type, str(e)[:50]))
            else:
                # Log missing API keys at debug level (not error - keys are optional)
                pass  # User may not have all providers configured

        # Initialize Ollama (no API key needed - runs locally)
        try:
            if "ollama" in self.MODEL_IMPLEMENTATIONS:
                model_class = self.MODEL_IMPLEMENTATIONS["ollama"]
                model_instance = model_class(model_name=self.DEFAULT_MODELS["ollama"])

                if model_instance.is_available():
                    self._models["ollama"] = model_instance
                    cprint(f"   ✅ ollama: {model_instance.model_name} (local)", "green")
                    initialized_count += 1
                else:
                    # Not an error - Ollama is optional
                    cprint("   ⚪ ollama: Server not running (optional)", "white")
        except Exception as e:
            cprint(f"   ⚪ ollama: Not available - {str(e)[:30]}", "white")

        # Initialize OllamaFreeAPI (no API key needed - free cloud service)
        try:
            if "ollamafreeapi" in self.MODEL_IMPLEMENTATIONS:
                model_class = self.MODEL_IMPLEMENTATIONS["ollamafreeapi"]
                model_instance = model_class(model_name=self.DEFAULT_MODELS["ollamafreeapi"])

                if model_instance.is_available():
                    self._models["ollamafreeapi"] = model_instance
                    cprint(f"   ✅ ollamafreeapi: {model_instance.model_name} (FREE)", "green")
                    initialized_count += 1
                else:
                    cprint("   ⚪ ollamafreeapi: Service not available", "white")
        except Exception as e:
            cprint(f"   ⚪ ollamafreeapi: {str(e)[:30]}", "white")

        # Summary
        cprint(f"\n📊 Model Factory Summary:", "cyan")
        cprint(f"   • {initialized_count} providers ready", "green" if initialized_count > 0 else "yellow")
        cprint(f"   • {len(self.MODEL_IMPLEMENTATIONS)} providers supported", "cyan")

        if failed_models:
            cprint(f"   • {len(failed_models)} providers failed:", "yellow")
            for model_type, error in failed_models[:3]:  # Show first 3 failures
                cprint(f"     - {model_type}: {error}", "yellow")

        if not self._models:
            cprint("\n⚠️ No AI models available!", "yellow", attrs=["bold"])
            cprint("   Check your .env file for API keys:", "yellow")
            cprint("   • GEMINI_KEY (recommended - free tier)", "cyan")
            cprint("   • ANTHROPIC_KEY, OPENAI_KEY, etc.", "cyan")
        else:
            cprint(f"\n✨ Ready to use: {', '.join(self._models.keys())}", "green")
    
    def get_model(self, model_type: str, model_name: Optional[str] = None) -> Optional[BaseModel]:
        """Get a specific model instance

        This method handles dynamic model initialization - even if a model wasn't
        available at startup (e.g., API key not set), it can be initialized later
        when the key becomes available (e.g., via BYOK).
        """
        if model_type not in self.MODEL_IMPLEMENTATIONS:
            cprint(f"⚠️ Unknown model type: {model_type}", "yellow")
            return None

        # If model not yet initialized, try to initialize it now
        # This handles the case where API keys are added via BYOK after startup
        if model_type not in self._models:
            try:
                # Special handling for models that don't need API keys
                if model_type in ("ollama", "ollamafreeapi"):
                    model_class = self.MODEL_IMPLEMENTATIONS[model_type]
                    default_model = model_name or self.DEFAULT_MODELS.get(model_type)
                    model_instance = model_class(model_name=default_model)
                    if model_instance.is_available():
                        self._models[model_type] = model_instance
                        cprint(f"✅ {model_instance.model_name} initialized on-demand", "green")
                else:
                    # For API-based models, check if we now have an API key
                    key_mapping = self._get_api_key_mapping()
                    if model_type in key_mapping:
                        if api_key := os.getenv(key_mapping[model_type]):
                            model_class = self.MODEL_IMPLEMENTATIONS[model_type]
                            default_model = model_name or self.DEFAULT_MODELS.get(model_type)
                            model_instance = model_class(api_key, model_name=default_model)
                            if model_instance.is_available():
                                self._models[model_type] = model_instance
                                cprint(f"✅ {model_instance.model_name} initialized on-demand", "green")
            except Exception as e:
                cprint(f"⚠️ Failed to initialize {model_type}: {e}", "yellow")
                return None

        if model_type not in self._models:
            return None

        model = self._models[model_type]
        if model_name and model.model_name != model_name:
            try:
                # Special handling for models that don't need API keys
                if model_type in ("ollama", "ollamafreeapi"):
                    model = self.MODEL_IMPLEMENTATIONS[model_type](model_name=model_name)
                else:
                    # For API-based models that need a key
                    if api_key := os.getenv(self._get_api_key_mapping()[model_type]):
                        model = self.MODEL_IMPLEMENTATIONS[model_type](api_key, model_name=model_name)
                    else:
                        return None

                self._models[model_type] = model
            except:
                return None

        return model
    
    def _get_api_key_mapping(self) -> Dict[str, str]:
        """Get mapping of model types to their API key environment variable names"""
        return {
            "claude": "ANTHROPIC_KEY",
            "groq": "GROQ_API_KEY",
            "openai": "OPENAI_KEY",
            "gemini": "GEMINI_KEY",  # Re-enabled with Gemini 2.5 models
            "deepseek": "DEEPSEEK_KEY",
            "xai": "XAI_KEY",  # xAI uses XAI_KEY (aligned with secrets_manager.py)
            "openrouter": "OPENROUTER_API_KEY",  # 🌙 Moon Dev: OpenRouter - 200+ models!
            # Ollama doesn't need an API key as it runs locally
        }
    
    @property
    def available_models(self) -> Dict[str, list]:
        """Get all available models and their configurations"""
        return {
            model_type: model.AVAILABLE_MODELS
            for model_type, model in self._models.items()
        }
    
    def is_model_available(self, model_type: str) -> bool:
        """Check if a specific model type is available"""
        return model_type in self._models and self._models[model_type].is_available()

# Create a singleton instance
model_factory = ModelFactory() 