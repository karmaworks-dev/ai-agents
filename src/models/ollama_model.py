"""
🌙 Moon Dev's Ollama Model Integration
Built with love by Moon Dev 🚀

This module provides integration with locally running Ollama models.
"""

import requests
import json
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class OllamaModel(BaseModel):
    """Implementation for local Ollama models

    Requires Ollama to be running locally: ollama serve
    Install models with: ollama pull <model_name>
    """

    # Ollama server configuration
    DEFAULT_BASE_URL = "http://localhost:11434/api"

    # Available Ollama models - can be expanded based on what's installed locally
    # Dict format for consistency with other model providers
    # Priority: Quantized DeepSeek models for trading (memory efficient)
    # To install: ollama pull <model_name>
    AVAILABLE_MODELS = {
        # ===== DeepSeek V3.2 (RECOMMENDED for Trading) =====
        "deepseek-v3.2:671b-q4_K_M": {
            "description": "DeepSeek V3.2 671B Quantized - Best trading model (Q4_K_M)",
            "parameters": "671B",
            "recommended": True
        },
        "deepseek-v3.2": {
            "description": "DeepSeek V3.2 - Latest flagship (671B parameters)",
            "parameters": "671B",
            "recommended": True
        },
        # ===== DeepSeek V3.1 (Stable for Trading) =====
        "deepseek-v3.1:671b": {
            "description": "DeepSeek V3.1 671B - Stable trading model ⚡ Recommended",
            "parameters": "671B",
            "recommended": True
        },
        "deepseek-v3.1:671b-q4_K_M": {
            "description": "DeepSeek V3.1 671B Quantized - Memory efficient",
            "parameters": "671B"
        },
        # ===== DeepSeek Reasoning Models =====
        "deepseek-r1": {
            "description": "DeepSeek R1 - Reasoning model (7B parameters, local)",
            "parameters": "7B"
        },
        "deepseek-r1:14b": {
            "description": "DeepSeek R1 14B - Enhanced reasoning (14B parameters)",
            "parameters": "14B"
        },
        "deepseek-r1:32b": {
            "description": "DeepSeek R1 32B - Strong reasoning (32B parameters)",
            "parameters": "32B"
        },
        # ===== DeepSeek Coder =====
        "deepseek-coder": {
            "description": "DeepSeek Coder - STEM and code expert (6.7B parameters, local)",
            "parameters": "6.7B"
        },
        "deepseek-coder:33b": {
            "description": "DeepSeek Coder 33B - Advanced coding (33B parameters)",
            "parameters": "33B"
        },
        # ===== Qwen Models =====
        "qwen3:8b": {
            "description": "Qwen 3 8B - Fast reasoning model (8B parameters, local)",
            "parameters": "8B"
        },
        "qwen3:14b": {
            "description": "Qwen 3 14B - Balanced performance (14B parameters)",
            "parameters": "14B"
        },
        "qwen3:32b": {
            "description": "Qwen 3 32B - Strong reasoning (32B parameters)",
            "parameters": "32B"
        },
        # ===== LLaMA Models =====
        "llama3.2": {
            "description": "Meta Llama 3.2 - Fast and efficient (default, local)",
            "parameters": "8B"
        },
        "llama3.3:70b": {
            "description": "Meta Llama 3.3 70B - Large model (70B parameters)",
            "parameters": "70B"
        },
        # ===== Other Models =====
        "mistral": {
            "description": "Mistral - General purpose model (7B parameters, local)",
            "parameters": "7B"
        },
        "gemma:2b": {
            "description": "Google Gemma 2B - Lightweight model (2B parameters, local)",
            "parameters": "2B"
        },
    }
    
    def __init__(self, api_key=None, model_name="deepseek-v3.1:671b-q4_K_M", base_url=None):
        """Initialize Ollama model

        Args:
            api_key: Not used for Ollama but kept for compatibility
            model_name: Name of the Ollama model to use (default: quantized DeepSeek V3.1)
            base_url: Custom Ollama API endpoint (default: http://localhost:11434/api)
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model_name = model_name
        self._is_connected = False
        self._connection_error = None
        self._available_models = []

        # Pass a dummy API key to satisfy BaseModel
        super().__init__(api_key="LOCAL_OLLAMA")
        self.initialize_client()

    def initialize_client(self):
        """Initialize the Ollama client connection

        This method handles connection errors gracefully without raising exceptions.
        Check self._is_connected to verify connection status.
        """
        self._is_connected = False
        self._connection_error = None

        try:
            response = requests.get(f"{self.base_url}/tags", timeout=5)
            if response.status_code == 200:
                self._is_connected = True
                cprint(f"✨ Connected to Ollama server at {self.base_url}", "green")

                # Get available models
                models = response.json().get("models", [])
                if models:
                    self._available_models = [model["name"] for model in models]
                    cprint(f"📚 {len(self._available_models)} models available locally", "cyan")

                    # Check if requested model is available
                    if self.model_name not in self._available_models:
                        # Try partial match (e.g., "deepseek-v3.1" matches "deepseek-v3.1:671b")
                        partial_matches = [m for m in self._available_models if self.model_name in m or m in self.model_name]
                        if partial_matches:
                            cprint(f"   Using closest match: {partial_matches[0]}", "cyan")
                            self.model_name = partial_matches[0]
                        else:
                            cprint(f"⚠️ Model '{self.model_name}' not found locally!", "yellow")
                            cprint(f"   Install it with: ollama pull {self.model_name}", "yellow")
                            cprint(f"   Available models: {self._available_models[:5]}...", "cyan")
                else:
                    cprint("⚠️ No models installed! Pull a model first:", "yellow")
                    cprint(f"   ollama pull {self.model_name}", "yellow")
            else:
                self._connection_error = f"Ollama API returned status code: {response.status_code}"
                cprint(f"⚠️ {self._connection_error}", "yellow")

        except requests.exceptions.ConnectionError:
            self._connection_error = "Ollama server not running"
            cprint("⚠️ Ollama server not running at {self.base_url}", "yellow")
            cprint("   💡 Start with: ollama serve", "cyan")
            cprint("   💡 Or use 'ollamafreeapi' or 'gemini' providers instead (no local server needed)", "cyan")

        except requests.exceptions.Timeout:
            self._connection_error = "Connection timeout"
            cprint("⚠️ Ollama server connection timed out", "yellow")

        except Exception as e:
            self._connection_error = str(e)
            cprint(f"⚠️ Ollama connection error: {str(e)}", "yellow")

    @property
    def model_type(self):
        """Return the type of model"""
        return "ollama"

    def is_available(self):
        """Check if the Ollama server is connected and available"""
        return self._is_connected

    def get_connection_status(self):
        """Get detailed connection status

        Returns:
            dict with keys:
                - connected: bool
                - error: str or None
                - available_models: list of model names
                - base_url: str
        """
        return {
            "connected": self._is_connected,
            "error": self._connection_error,
            "available_models": self._available_models,
            "base_url": self.base_url,
            "current_model": self.model_name
        }

    def reconnect(self):
        """Attempt to reconnect to the Ollama server"""
        cprint("🔄 Attempting to reconnect to Ollama server...", "cyan")
        self.initialize_client()
        return self._is_connected
    
    def generate_response(self, system_prompt, user_content, temperature=0.7, max_tokens=None, **kwargs):
        """Generate a response using the Ollama model

        Args:
            system_prompt: System prompt to guide the model
            user_content: User's input content
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (ignored by Ollama, kept for compatibility)
            **kwargs: Additional arguments (ignored, kept for compatibility)

        Returns:
            ModelResponse object (always returns ModelResponse, never None)
        """
        # Check if connected, attempt reconnect if not
        if not self._is_connected:
            self.reconnect()
            if not self._is_connected:
                return ModelResponse(
                    content="",
                    raw_response={"error": f"Ollama server not available: {self._connection_error}"},
                    model_name=self.model_name,
                    usage=None
                )

        try:
            # Format the prompt with system and user content
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            # Prepare the request
            data = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            # Make the request with 90 second timeout
            response = requests.post(
                f"{self.base_url}/chat",
                json=data,
                timeout=90  # Match swarm timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                raw_content = response_data.get("message", {}).get("content", "")

                # Remove <think>...</think> tags and their content (Qwen reasoning)
                import re

                # First, try to remove complete <think>...</think> blocks
                filtered_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()

                # If <think> tag exists but wasn't removed (unclosed tag due to token limit),
                # remove everything from <think> onwards
                if '<think>' in filtered_content:
                    filtered_content = filtered_content.split('<think>')[0].strip()

                # If filtering removed everything, return the original (in case it's not a Qwen model)
                final_content = filtered_content if filtered_content else raw_content

                return ModelResponse(
                    content=final_content,
                    raw_response=response_data,
                    model_name=self.model_name,
                    usage=None  # Ollama doesn't provide token usage info
                )
            else:
                cprint(f"❌ Ollama API error: {response.status_code}", "red")
                cprint(f"Response: {response.text}", "red")
                raise Exception(f"Ollama API error: {response.status_code}")

        except Exception as e:
            cprint(f"❌ Error generating response: {str(e)}", "red")
            # Don't re-raise - let swarm agent handle failed responses gracefully
            return ModelResponse(
                content="",
                raw_response={"error": str(e)},
                model_name=self.model_name,
                usage=None
            )
    
    def __str__(self):
        return f"OllamaModel(model={self.model_name})"

    def get_model_parameters(self, model_name=None):
        """Get the parameter count for a specific model

        Args:
            model_name: Name of the model to check (defaults to self.model_name)

        Returns:
            String with parameter count (e.g., "7B", "13B") or None if not available
        """
        if model_name is None:
            model_name = self.model_name

        try:
            # Check AVAILABLE_MODELS dict for parameter info
            if model_name in self.AVAILABLE_MODELS:
                return self.AVAILABLE_MODELS[model_name].get("parameters", "Unknown")

            return "Unknown"
        except Exception as e:
            cprint(f"❌ Error getting model parameters: {str(e)}", "red")
            return None 