# 🌙 Moon Dev's Model Factory

A unified interface for managing multiple AI model providers. This module handles initialization, API key management, and provides a consistent interface for generating responses across different AI models.

## 🔑 Required API Keys

Add these to your `.env` file in the project root:
```env
ANTHROPIC_KEY=your_key_here    # For Claude models
GROQ_API_KEY=your_key_here     # For Groq models (includes Mixtral, Llama, etc.)
OPENAI_KEY=your_key_here       # For OpenAI models (GPT-4, O1, etc.)
GEMINI_KEY=your_key_here       # For Gemini models
DEEPSEEK_KEY=your_key_here     # For DeepSeek models
```

## 🤖 Available Models

### OpenAI Models
Latest Models:
- `gpt-5`: Next-generation GPT model (use when you want the strongest reasoning + code generation)
- `gpt-4o`: Latest GPT-4 Optimized model (Best for complex reasoning)
- `gpt-4o-mini`: Smaller, faster GPT-4 Optimized model (Good balance of speed/quality)
- `o1`: Latest O1 model (Dec 2024) - Shows reasoning process
- `o1-mini`: Smaller O1 model - Shows reasoning process
- `o3-mini`: Brand new fast reasoning model

### Claude Models (Anthropic)
Latest Models:
- `claude-3-opus-20240229`: Most powerful Claude model (Best for complex tasks)
- `claude-3-sonnet-20240229`: Balanced Claude model (Good for most use cases)
- `claude-3-haiku-20240307`: Fast, efficient Claude model (Best for quick responses)

### Gemini Models (Google)
Latest Models:
- `gemini-2.0-flash-exp`: Next-gen multimodal model (Audio, images, video, text)
- `gemini-2.0-flash`: Fast, efficient model optimized for quick responses
- `gemini-1.5-flash`: Fast versatile model (Audio, images, video, text)
- `gemini-1.5-flash-8b`: High volume tasks (Audio, images, video, text)
- `gemini-1.5-pro`: Complex reasoning tasks (Audio, images, video, text)
- `gemini-1.0-pro`: Natural language & code (Deprecated 2/15/2025)
- `text-embedding-004`: Text embeddings model

### Groq Models
Production Models:
- `mixtral-8x7b-32768`: Mixtral 8x7B (32k context) - $0.27/1M tokens
- `gemma2-9b-it`: Google Gemma 2 9B (8k context) - $0.10/1M tokens
- `llama-3.3-70b-versatile`: Llama 3.3 70B (128k context) - $0.70/1M in, $0.90/1M out
- `llama-3.1-8b-instant`: Llama 3.1 8B (128k context) - $0.10/1M tokens
- `llama-guard-3-8b`: Llama Guard 3 8B (8k context) - $0.20/1M tokens
- `llama3-70b-8192`: Llama 3 70B (8k context) - $0.70/1M in, $0.90/1M out
- `llama3-8b-8192`: Llama 3 8B (8k context) - $0.10/1M tokens

Preview Models:
- `deepseek-r1-distill-llama-70b`: DeepSeek R1 (128k context) - Shows thinking process
- `llama-3.3-70b-specdec`: Llama 3.3 70B SpecDec (8k context)
- `llama-3.2-1b-preview`: Llama 3.2 1B (128k context)
- `llama-3.2-3b-preview`: Llama 3.2 3B (128k context)

### DeepSeek Models
- `deepseek-chat`: Fast chat model (Good for conversational tasks)
- `deepseek-reasoner`: Enhanced reasoning model (Better for complex problem-solving)
- `deepseek-r1`: DeepSeek's first-generation reasoning model (Excellent for trading strategies)

### OllamaFreeAPI: 650+ FREE Models in the Cloud 🌐

**No API key required!** Access 650+ models for free via the OllamaFreeAPI service.

Installation:
```bash
pip install ollamafreeapi
```

Available Models (Recommended):
- `deepseek-coder:6.7b`: **⚡ RECOMMENDED** - STEM and coding expert (6.7B parameters)
- `deepseek-coder:33b`: Advanced coding model (33B parameters)
- `deepseek-r1:7b`: Reasoning model (7B parameters)
- `llama3:8b-instruct`: General purpose model (8B parameters)
- `llama3.3:70b`: Large general model (70B parameters)
- `llama3:code`: Coding specialized model
- `mistral:7b-v0.2`: Efficient general model (7B parameters)
- `qwen:7b-chat`: Alibaba chat model (7B parameters)
- `qwen:14b-chat`: Larger Qwen model (14B parameters)

Benefits:
- 🆓 Completely FREE - no API keys needed!
- 🌐 Cloud-hosted - no local setup required
- 📊 650+ models available
- 🧠 DeepSeek Coder for STEM/math tasks
- ⚡ Fast inference

Usage Example:
```python
from src.models import model_factory

# Use DeepSeek Coder for STEM/coding (FREE & Recommended)
model = model_factory.get_model("ollamafreeapi", "deepseek-coder:6.7b")

# Or use LLaMA 3 for general tasks (FREE)
model = model_factory.get_model("ollamafreeapi", "llama3:8b-instruct")
```

Rate Limits (Free Tier):
- 100 requests per hour
- 16k tokens per request

---

### Local Ollama: Free, Fast, Private LLMs 🚀

Run AI models locally on your machine for complete privacy and no rate limits.

To get started with Ollama:
1. Install Ollama: `curl https://ollama.ai/install.sh | sh`
2. Start the server: `ollama serve`
3. Pull models:
   ```bash
   ollama pull deepseek-r1      # DeepSeek R1 7B - shows thinking process
   ollama pull deepseek-coder   # DeepSeek Coder - STEM/code expert
   ollama pull gemma:2b         # Google's Gemma 2B - fast responses
   ollama pull llama3.2         # Meta's Llama 3.2 - balanced performance
   ollama pull mistral          # Mistral 7B - general purpose
   ```
4. Check they're ready: `ollama list`

Available Models:
- `deepseek-r1`: Complex reasoning (7B), shows thinking process with <think> tags
- `deepseek-coder`: STEM and code expert (6.7B)
- `gemma:2b`: Fast and efficient for simple tasks
- `llama3.2`: Balanced model, good at following instructions
- `mistral`: General purpose model (7B)
- `qwen3:8b`: Fast reasoning model (8B)

Benefits:
- 🚀 Free to use - no API costs
- 🔒 Private - runs 100% local
- ⚡ No rate limits
- 🤔 DeepSeek shows thinking process
- 🛠️ Full model control

Usage Example:
```python
from src.models import model_factory

# Initialize with Llama 3.2 for balanced performance
model = model_factory.get_model("ollama", "llama3.2")

# Or use DeepSeek Coder for STEM/coding
model = model_factory.get_model("ollama", "deepseek-coder")

# Or Gemma for faster responses
model = model_factory.get_model("ollama", "gemma:2b")
```

## 🚀 Usage Example

```python
from src.models import model_factory

# Initialize the model factory
factory = model_factory.ModelFactory()

# Get a specific model
model = factory.get_model("openai", "gpt-4o")  # Using latest GPT-4 Optimized

# Generate a response
response = model.generate_response(
    system_prompt="You are a helpful AI assistant.",
    user_content="Hello!",
    temperature=0.7,  # Optional: Control randomness (0.0-1.0)
    max_tokens=1024   # Optional: Control response length
)

print(response.content)
```

## 🌟 Features
- Unified interface for multiple AI providers
- Automatic API key validation and error handling
- Detailed debugging output with emojis
- Easy model switching with consistent interface
- Consistent response format across all providers
- Automatic handling of model-specific features:
  - Reasoning process display (O1, DeepSeek R1)
  - Context window management
  - Token counting and limits
  - Error recovery and retries

## 🔄 Model Updates
New models are regularly added to the factory. Check the Moon Dev Discord or GitHub for announcements about new models and features.

## 🐛 Troubleshooting
- If a model fails to initialize, check your API key in the `.env` file
- Some models (O1, DeepSeek R1) show their thinking process - this is normal
- For rate limit errors, try using a different model or wait a few minutes
- Watch Moon Dev's streams for live debugging and updates: [@moondevonyt](https://www.youtube.com/@moondevonyt)

## 🤝 Contributing
Feel free to contribute new models or improvements! Join the Moon Dev community:
- YouTube: [@moondevonyt](https://www.youtube.com/@moondevonyt)
- GitHub: [moon-dev-ai-agents-for-trading](https://github.com/moon-dev-ai-agents-for-trading)

Built with 💖 by Moon Dev 🌙
