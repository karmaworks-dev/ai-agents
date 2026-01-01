"""
🌙 Moon Dev's OllamaFreeAPI Model Integration
Built with love by Moon Dev 🚀

This module provides integration with the free OllamaFreeAPI service.
Access 650+ AI models without API keys - perfect for testing and development!

Install: pip install ollamafreeapi
"""

from termcolor import cprint
from .base_model import BaseModel, ModelResponse


class OllamaFreeAPIModel(BaseModel):
    """Implementation for OllamaFreeAPI - free access to 650+ models"""

    # Available models through OllamaFreeAPI
    # These are the most stable and recommended models
    AVAILABLE_MODELS = {
        # DeepSeek Models - STEM and Coding experts
        "deepseek-r1:7b": {
            "description": "DeepSeek R1 7B - Reasoning model (FREE, 7B parameters)",
            "parameters": "7B",
            "specialty": "reasoning"
        },
        "deepseek-coder:6.7b": {
            "description": "DeepSeek Coder - STEM and code expert (FREE, 6.7B) ⚡ Recommended",
            "parameters": "6.7B",
            "specialty": "coding"
        },
        "deepseek-coder:33b": {
            "description": "DeepSeek Coder 33B - Advanced coding model (FREE, 33B)",
            "parameters": "33B",
            "specialty": "coding"
        },

        # LLaMA Models - Meta's open models
        "llama3:8b-instruct": {
            "description": "LLaMA 3 8B Instruct - General purpose (FREE, 8B)",
            "parameters": "8B",
            "specialty": "general"
        },
        "llama3.3:70b": {
            "description": "LLaMA 3.3 70B - Large general model (FREE, 70B)",
            "parameters": "70B",
            "specialty": "general"
        },
        "llama3:code": {
            "description": "LLaMA 3 Code - Coding specialized (FREE)",
            "parameters": "8B",
            "specialty": "coding"
        },

        # Mistral Models
        "mistral:7b-v0.2": {
            "description": "Mistral 7B v0.2 - Efficient general model (FREE, 7B)",
            "parameters": "7B",
            "specialty": "general"
        },
        "mistral:storyteller": {
            "description": "Mistral Storyteller - Creative writing (FREE, 7B)",
            "parameters": "7B",
            "specialty": "creative"
        },

        # Qwen Models
        "qwen:7b-chat": {
            "description": "Qwen 7B Chat - Alibaba's chat model (FREE, 7B)",
            "parameters": "7B",
            "specialty": "chat"
        },
        "qwen:14b-chat": {
            "description": "Qwen 14B Chat - Larger Qwen model (FREE, 14B)",
            "parameters": "14B",
            "specialty": "chat"
        },
    }

    def __init__(self, api_key=None, model_name="deepseek-coder:6.7b", **kwargs):
        """Initialize OllamaFreeAPI model

        Args:
            api_key: Not used - OllamaFreeAPI is free! Kept for compatibility.
            model_name: Name of the model to use (default: deepseek-coder:6.7b)
        """
        self.model_name = model_name
        self.client = None
        self.max_tokens = kwargs.get('max_tokens', 2000)
        # Pass dummy API key to satisfy BaseModel
        super().__init__(api_key="FREE_API_NO_KEY_REQUIRED", **kwargs)

    def initialize_client(self, **kwargs) -> None:
        """Initialize the OllamaFreeAPI client"""
        try:
            from ollamafreeapi import OllamaFreeAPI
            self.client = OllamaFreeAPI()

            # Test connection by listing models
            cprint(f"✨ OllamaFreeAPI connected - using {self.model_name}", "green")
            cprint("   💡 Free tier: 100 requests/hour, 16k tokens", "cyan")

        except ImportError:
            cprint("❌ ollamafreeapi not installed. Run: pip install ollamafreeapi", "red")
            self.client = None
        except Exception as e:
            cprint(f"❌ Failed to initialize OllamaFreeAPI: {str(e)}", "red")
            self.client = None

    def generate_response(self, system_prompt, user_content, temperature=0.7, max_tokens=None, **kwargs):
        """Generate response using OllamaFreeAPI

        Args:
            system_prompt: System prompt to guide the model
            user_content: User's input content
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments

        Returns:
            ModelResponse with the generated content
        """
        if not self.client:
            cprint("❌ OllamaFreeAPI client not initialized", "red")
            return ModelResponse(
                content="",
                raw_response={"error": "Client not initialized"},
                model_name=self.model_name,
                usage=None
            )

        try:
            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_content}"

            # Call the API
            response = self.client.chat(
                model_name=self.model_name,
                prompt=full_prompt,
                temperature=temperature
            )

            # Extract content from response
            if isinstance(response, dict):
                content = response.get('response', '') or response.get('message', {}).get('content', '')
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)

            # Filter reasoning tags if present (for DeepSeek models)
            import re
            filtered_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            if '<think>' in filtered_content:
                filtered_content = filtered_content.split('<think>')[0].strip()
            final_content = filtered_content if filtered_content else content

            return ModelResponse(
                content=final_content,
                raw_response=response,
                model_name=self.model_name,
                usage=None  # OllamaFreeAPI doesn't provide token usage
            )

        except Exception as e:
            error_str = str(e)

            # Handle rate limit errors
            if "rate" in error_str.lower() or "limit" in error_str.lower():
                cprint("⚠️  OllamaFreeAPI rate limit reached (100 req/hour)", "yellow")
                cprint("   💡 Wait a few minutes or switch to local Ollama", "cyan")
                return None

            cprint(f"❌ OllamaFreeAPI error: {error_str}", "red")
            return ModelResponse(
                content="",
                raw_response={"error": error_str},
                model_name=self.model_name,
                usage=None
            )

    def is_available(self) -> bool:
        """Check if OllamaFreeAPI is available"""
        return self.client is not None

    @property
    def model_type(self) -> str:
        return "ollamafreeapi"

    def list_available_models(self):
        """List all available models from the API"""
        if not self.client:
            return list(self.AVAILABLE_MODELS.keys())

        try:
            models = self.client.list_models()
            return models if models else list(self.AVAILABLE_MODELS.keys())
        except Exception:
            return list(self.AVAILABLE_MODELS.keys())

    def __str__(self):
        return f"OllamaFreeAPIModel(model={self.model_name})"
