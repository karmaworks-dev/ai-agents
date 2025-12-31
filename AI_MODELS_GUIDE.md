# AI Models Reference Guide - BYOK Platform
## Bring Your Own Key (BYOK) - User Settings Configuration

*Last Updated: December 2025*

---

## Overview

The AI trading system now supports **BYOK (Bring Your Own Key)** functionality, allowing you to:
- Choose your preferred AI provider (Company)
- Select specific AI models by their API names
- Configure temperature and token limits
- Switch models seamlessly from the frontend settings

---

## Configuration

### User Settings Structure

The user settings (`src/data/user_settings.json`) now include AI model configuration:

```json
{
  "timeframe": "5m",
  "days_back": 1,
  "sleep_minutes": 5,

  "ai_provider": "gemini",
  "ai_model": "gemini-2.5-flash",
  "ai_temperature": 0.3,
  "ai_max_tokens": 2000,

  "last_updated": "2025-12-31T10:06:01.116005"
}
```

### Settings Parameters

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `ai_provider` | string | See providers below | AI company/provider name |
| `ai_model` | string | See models below | Exact API model name |
| `ai_temperature` | float | 0.0 - 1.0 | Creativity (0.0 = deterministic, 1.0 = creative) |
| `ai_max_tokens` | integer | 100 - 100000 | Maximum response length |

---

## Supported AI Providers

### 1. Anthropic (Claude)
**Provider ID:** `anthropic`
**API Key:** `ANTHROPIC_KEY` (in `.env`)
**Recommended for:** General trading analysis, reasoning tasks

| Model API Name | Description | Context | Best For |
|----------------|-------------|---------|----------|
| `claude-sonnet-4-5-20250929` | Claude Sonnet 4.5 | 200K | ⚡ **Recommended** - Best balance |
| `claude-opus-4-5-20251101` | Claude Opus 4.5 | 200K | Most powerful reasoning |
| `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | 200K | Fastest, lowest cost |

---

### 2. OpenAI (GPT)
**Provider ID:** `openai`
**API Key:** `OPENAI_KEY` (in `.env`)
**Recommended for:** Complex reasoning, code generation

| Model API Name | Description | Context | Best For |
|----------------|-------------|---------|----------|
| `gpt-5.2` | GPT-5.2 Latest | 400K | Latest flagship |
| `gpt-5` | GPT-5 | 400K | Frontier model |
| `gpt-4.1` | GPT-4.1 | 1M | Large context tasks |
| `o3` | o3 Reasoning | 200K | Advanced reasoning |
| `o4-mini` | o4-mini | 200K | Latest reasoning |

---

### 3. Google (Gemini) ⚡ Default
**Provider ID:** `gemini`
**API Key:** `GEMINI_KEY` (in `.env`)
**Recommended for:** Fast trading decisions, cost-effective

| Model API Name | Description | Context | Best For |
|----------------|-------------|---------|----------|
| `gemini-2.5-flash` | Gemini 2.5 Flash | 1M | ⚡ **Recommended** - Fast trading |
| `gemini-3-pro` | Gemini 3 Pro | 1M | Latest flagship |
| `gemini-3-flash` | Gemini 3 Flash | 1M | Fast, cost-effective |
| `gemini-2.5-pro` | Gemini 2.5 Pro | 1M | Powerful, stable |
| `gemini-2.5-flash-lite` | Gemini 2.5 Flash-Lite | 1M | Ultra-efficient |
| `gemini-2.0-flash` | Gemini 2.0 Flash | 1M | Multimodal |

---

### 4. xAI (Grok)
**Provider ID:** `xai`
**API Key:** `GROK_API_KEY` (in `.env`)
**Recommended for:** Real-time analysis with X integration

| Model API Name | Description | Context | Best For |
|----------------|-------------|---------|----------|
| `grok-4-1-fast-reasoning` | Grok 4.1 Thinking | 2M | Best overall |
| `grok-4-1-fast-non-reasoning` | Grok 4.1 Instant | 2M | Instant responses |
| `grok-code-fast-1` | Grok Code Fast | 256K | Coding optimized |

---

### 5. DeepSeek
**Provider ID:** `deepseek`
**API Key:** `DEEPSEEK_KEY` (in `.env`)
**Recommended for:** Cost-effective reasoning, research

| Model API Name | Description | Context | Best For |
|----------------|-------------|---------|----------|
| `deepseek-chat` | DeepSeek V3 | 128K | ⚡ **Recommended** - General use |
| `deepseek-thinking-v3.2-exp` | DeepSeek V3.2 Thinking | 128K | Latest reasoning |
| `deepseek-reasoner` | DeepSeek R1 | 128K | Open reasoning |

---

### 6. Mistral AI
**Provider ID:** `mistral`
**API Key:** `MISTRAL_KEY` (in `.env`)
**Recommended for:** European data compliance, coding

| Model API Name | Description | Context | Best For |
|----------------|-------------|---------|----------|
| `mistral-small-latest` | Mistral Small | 128K | ⚡ **Recommended** - Cost-effective |
| `mistral-large-latest` | Mistral Large 3 | 256K | Flagship (41B active) |
| `devstral-2` | Devstral 2 | 256K | Coding (123B) |

---

### 7. Groq (Fast Inference)
**Provider ID:** `groq`
**API Key:** `GROQ_API_KEY` (in `.env`)
**Recommended for:** Ultra-fast inference, low latency

| Model API Name | Description | Context | Best For |
|----------------|-------------|---------|----------|
| `mixtral-8x7b-32768` | Mixtral 8x7B | 32K | Fast inference |
| `llama-3.3-70b-versatile` | Llama 3.3 70B | 128K | Versatile tasks |

---

### 8. Ollama (Local Models)
**Provider ID:** `ollama`
**No API Key Required** (runs locally)
**Recommended for:** Privacy, offline usage, no API costs

| Model API Name | Description | Best For |
|----------------|-------------|----------|
| `deepseek-chat` | DeepSeek Chat | Local reasoning |
| `llama3.2` | Llama 3.2 | Balanced performance |
| `qwen/qwen3:8b` | Qwen3 8B | Fast reasoning |

---

## Quick Start Guide

### 1. Set Up API Keys (Required)

Edit your `.env` file and add your API keys:

```bash
# Choose your provider and add the corresponding key
ANTHROPIC_KEY=sk-ant-...
OPENAI_KEY=sk-...
GEMINI_KEY=AI...
GROK_API_KEY=xai-...
DEEPSEEK_KEY=sk-...
```

### 2. Configure User Settings

**Option A: Via Dashboard (Frontend)**
1. Navigate to Settings page
2. Select AI Provider from dropdown
3. Select AI Model from available models
4. Adjust temperature (0.3 recommended for trading)
5. Set max tokens (2000 default)
6. Click "Save Settings"

**Option B: Via JSON File**

Edit `src/data/user_settings.json`:

```json
{
  "ai_provider": "gemini",
  "ai_model": "gemini-2.5-flash",
  "ai_temperature": 0.3,
  "ai_max_tokens": 2000
}
```

### 3. API Endpoints for Frontend

**Get All Available Models:**
```
GET /api/ai-models
```

**Get Models for Specific Provider:**
```
GET /api/ai-models?provider=gemini
```

**Update Settings:**
```
POST /api/settings
Content-Type: application/json

{
  "timeframe": "5m",
  "days_back": 1,
  "sleep_minutes": 5,
  "ai_provider": "gemini",
  "ai_model": "gemini-2.5-flash",
  "ai_temperature": 0.3,
  "ai_max_tokens": 2000
}
```

---

## Model Selection Guide for Trading

### Best for Real-Time Trading (Low Latency)
- **Gemini 2.5 Flash** (`gemini-2.5-flash`) - ⚡ Recommended
- **Grok 4.1 Non-Reasoning** (`grok-4-1-fast-non-reasoning`)
- **DeepSeek Chat** (`deepseek-chat`)

### Best for Complex Analysis
- **Claude Opus 4.5** (`claude-opus-4-5-20251101`)
- **GPT-5.2** (`gpt-5.2`)
- **Gemini 3 Pro** (`gemini-3-pro`)

### Best for Cost-Effective Operation
- **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`)
- **DeepSeek Chat** (`deepseek-chat`)
- **Mistral Small** (`mistral-small-latest`)
- **Ollama (Local)** - Free, no API costs

### Best for Code Generation (Backtesting)
- **Devstral 2** (`devstral-2`)
- **Grok Code Fast** (`grok-code-fast-1`)
- **GPT-5.1 Codex Max** (`gpt-5.1-codex-max`)

---

## Temperature Guidelines

| Temperature | Behavior | Recommended For |
|-------------|----------|----------------|
| 0.0 - 0.3 | Deterministic, consistent | **Trading decisions** (Recommended) |
| 0.4 - 0.6 | Balanced creativity | General analysis |
| 0.7 - 1.0 | Creative, varied | Content generation, brainstorming |

**Default for Trading:** `0.3`

---

## Validation Rules

The system automatically validates your settings:

- **Provider:** Must be one of the supported providers
- **Model:** Must be a valid model API name for the selected provider
- **Temperature:** Must be between 0.0 and 1.0
- **Max Tokens:** Must be between 100 and 100,000

Invalid settings will return error messages with details.

---

## Troubleshooting

### Error: "Invalid AI provider"
- Check that `ai_provider` matches one of the supported providers exactly
- Provider names are lowercase (e.g., `gemini`, not `Gemini`)

### Error: "Invalid model for provider"
- Verify the model API name matches exactly (case-sensitive)
- Check the reference tables above for correct model names
- Use `/api/ai-models?provider=<name>` to see available models

### Error: "API key not found"
- Ensure the corresponding API key is set in your `.env` file
- Restart the application after updating `.env`

### Model not responding
- Verify API key is valid and has sufficient credits
- Check provider's status page for outages
- Try a different model from the same provider

---

## Migration Guide

### Updating from Previous Version

If upgrading from a version without BYOK support:

1. Your existing `user_settings.json` will be automatically migrated
2. Default values will be added:
   - `ai_provider`: `"gemini"`
   - `ai_model`: `"gemini-2.5-flash"`
   - `ai_temperature`: `0.3`
   - `ai_max_tokens`: `2000`
3. Ensure `GEMINI_KEY` is set in `.env` for default operation

---

## API Key Procurement

| Provider | Console URL |
|----------|-------------|
| Anthropic | https://console.anthropic.com |
| OpenAI | https://platform.openai.com |
| Google | https://aistudio.google.com |
| xAI | https://console.x.ai |
| DeepSeek | https://platform.deepseek.com |
| Mistral | https://console.mistral.ai |
| Groq | https://console.groq.com |

---

## Example Configurations

### Conservative Trading (Low Risk)
```json
{
  "ai_provider": "anthropic",
  "ai_model": "claude-sonnet-4-5-20250929",
  "ai_temperature": 0.2,
  "ai_max_tokens": 1500
}
```

### Aggressive Trading (Fast Decisions)
```json
{
  "ai_provider": "gemini",
  "ai_model": "gemini-2.5-flash",
  "ai_temperature": 0.4,
  "ai_max_tokens": 2000
}
```

### Budget-Conscious (Low Cost)
```json
{
  "ai_provider": "deepseek",
  "ai_model": "deepseek-chat",
  "ai_temperature": 0.3,
  "ai_max_tokens": 2000
}
```

### Privacy-Focused (Local Only)
```json
{
  "ai_provider": "ollama",
  "ai_model": "deepseek-chat",
  "ai_temperature": 0.3,
  "ai_max_tokens": 2000
}
```

---

## Notes

- Model availability and pricing change frequently - verify with provider
- Some models may require waitlist access or special permissions
- Context window sizes are approximate maximums
- API costs vary significantly between providers and models
- Always test with small amounts before deploying to production

---

**For more information:**
- See `src/utils/settings_manager.py` for implementation details
- See `src/models/model_factory.py` for model integration
- See `trading_app.py` for API endpoint implementations
