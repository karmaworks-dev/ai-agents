"""
🌙 Moon Dev's Model System
Built with love by Moon Dev 🚀

This module performs best-effort imports of optional model adapters
so the package can be imported even when some provider SDKs are
missing in the environment. Missing adapters are omitted from
`__all__` and set to `None`.
"""

from .base_model import BaseModel, ModelResponse
from termcolor import cprint

# Optional model adapters. Import them in try/except blocks so the
# package import doesn't fail when a provider SDK isn't installed.
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
    cprint(f"⚠️ Optional model 'claude_model' missing or failed to import: {e}", "yellow")

try:
    from .groq_model import GroqModel
except Exception as e:
    cprint(f"⚠️ Optional model 'groq_model' missing or failed to import: {e}", "yellow")

try:
    from .openai_model import OpenAIModel
except Exception as e:
    cprint(f"⚠️ Optional model 'openai_model' missing or failed to import: {e}", "yellow")

try:
    from .gemini_model import GeminiModel
except Exception as e:
    cprint(f"⚠️ Optional model 'gemini_model' missing or failed to import: {e}", "yellow")

try:
    from .deepseek_model import DeepSeekModel
except Exception as e:
    cprint(f"⚠️ Optional model 'deepseek_model' missing or failed to import: {e}", "yellow")

try:
    from .ollama_model import OllamaModel
except Exception as e:
    cprint(f"⚠️ Optional model 'ollama_model' missing or failed to import: {e}", "yellow")

try:
    from .ollamafreeapi_model import OllamaFreeAPIModel
except Exception as e:
    cprint(f"⚠️ Optional model 'ollamafreeapi_model' missing or failed to import: {e}", "yellow")

try:
    from .xai_model import XAIModel
except Exception as e:
    cprint(f"⚠️ Optional model 'xai_model' missing or failed to import: {e}", "yellow")

try:
    from .openrouter_model import OpenRouterModel
except Exception as e:
    cprint(f"⚠️ Optional model 'openrouter_model' missing or failed to import: {e}", "yellow")

from .model_factory import model_factory

__all__ = [
    'BaseModel',
    'ModelResponse',
    'ClaudeModel',
    'GroqModel',
    'OpenAIModel',
    'GeminiModel',
    'DeepSeekModel',
    'OllamaModel',
    'OllamaFreeAPIModel',
    'XAIModel',
    'OpenRouterModel',
    'model_factory'
]