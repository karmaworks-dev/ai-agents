"""
🌙 Moon Dev's Claude Model Implementation
Built with love by Moon Dev 🚀
"""

from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class ClaudeModel(BaseModel):
    """Implementation for Anthropic's Claude models"""
    
    AVAILABLE_MODELS = {
        # Claude 4 Series (New Generation) - 🌙 Moon Dev's Latest Models!
        # API names include date suffixes for version control
        "claude-opus-4-5-20251101": "Claude Opus 4.5 - Most powerful model with superior reasoning and creativity (200K context)",
        "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5 - Best balance of speed and intelligence (200K context) ⚡ Recommended",
        "claude-haiku-4-5-20251001": "Claude Haiku 4.5 - Fastest, lowest cost (200K context)",
        "claude-opus-4-20250514": "Claude Opus 4 - Powerful reasoning (200K context)",
        "claude-sonnet-4-20250514": "Claude Sonnet 4 - Fast, efficient (200K context)",

        # Claude 3 Series (Legacy Stable)
        "claude-3-5-sonnet-latest": "Latest Claude 3.5 Sonnet with enhanced performance",
        "claude-3-5-haiku-latest": "Latest Claude 3.5 Haiku - blazing fast",
        "claude-3-opus-latest": "Most powerful Claude 3 model",
        "claude-3-sonnet-latest": "Balanced Claude 3 model",
        "claude-3-haiku-latest": "Fast, efficient Claude 3 model"
    }
    
    def __init__(self, api_key: str, model_name: str = "claude-3-5-haiku-latest", **kwargs):
        self.model_name = model_name
        super().__init__(api_key, **kwargs)
    
    def initialize_client(self, **kwargs) -> None:
        """Initialize the Anthropic client"""
        try:
            from anthropic import Anthropic  # imported lazily to avoid hard dependency
        except Exception as e:
            cprint(f"⚠️ Anthropic SDK not available: {e}", "yellow")
            self.client = None
            return

        try:
            self.client = Anthropic(api_key=self.api_key)
            cprint(f"✨ Initialized Claude model: {self.model_name}", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize Claude model: {str(e)}", "red")
            self.client = None
    
    def generate_response(self, 
        system_prompt: str,
        user_content: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> ModelResponse:
        """Generate a response using Claude"""
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_content}
                ]
            )
            
            return ModelResponse(
                content=response.content[0].text.strip(),
                raw_response=response,
                model_name=self.model_name,
                usage={"completion_tokens": response.usage.output_tokens}
            )
            
        except Exception as e:
            cprint(f"❌ Claude generation error: {str(e)}", "red")
            raise
    
    def is_available(self) -> bool:
        """Check if Claude is available"""
        return self.client is not None
    
    @property
    def model_type(self) -> str:
        return "claude" 