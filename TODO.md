# TODO - Beta Launch Checklist

> **Current Version:** Pre-Beta (v0.9)
> **Target:** Beta Test Launch
> **Last Updated:** January 2026

---

## Overview

This document tracks all tasks required for the beta launch of the AI Trading Dashboard.

---

## Completed

### Core Bug Fixes

- [x] Fix xAI environment variable mismatch (`GROK_API_KEY` → `XAI_KEY`)
- [x] Fix `self.max_tokens` undefined error in `openrouter_model.py`
- [x] Fix `self.max_tokens` undefined error in `groq_model.py`
- [x] Fix `self.max_tokens` undefined error in `base_model.py`
- [x] Remove prompt corruption from `base_model.py` (nonce/timestamp injection was breaking AI responses)
- [x] Standardize Claude model names with date suffixes
- [x] Change Groq default model from preview to production (`mixtral-8x7b-32768`)
- [x] Convert Ollama `AVAILABLE_MODELS` from list to dict format

### AI Model Integration

- [x] Create `OllamaFreeAPIModel` for free cloud AI access (`src/models/ollamafreeapi_model.py`)
- [x] Add OllamaFreeAPI to `model_factory.py`
- [x] Add OllamaFreeAPI to `settings_manager.py`
- [x] Add OllamaFreeAPI to frontend provider dropdown
- [x] Fix `/api/ai-models` endpoint to include all providers
- [x] Create Ollama auto-install script (`scripts/setup_ollama.sh`)

### Tier System

- [x] Design tier data model (`src/utils/tier_manager.py`)
  - Based (Free): 5 tokens, 5min cycle, Single AI, Ollama only
  - Trader ($5/mo): 10 tokens, 5min cycle, BYOK enabled, All providers
  - Pro ($20/mo): Unlimited tokens, Any cycle, Swarm mode, Up to 6 AI models
- [x] Create tier API endpoints
  - `GET /api/tier` - Get current tier info
  - `POST /api/tier` - Update tier (admin only)
  - `POST /api/tier/validate` - Validate settings against tier
  - `GET /api/tier/features` - Get feature access
- [x] Create tier selection UI in Account modal (PLAN tab)
- [x] Implement tier enforcement with UI locking
  - Swarm mode radio locked for non-Pro users
  - Swarm models section locked for non-Pro users
  - BYOK section shows warning for Based tier
  - Token limit badge displayed
  - Provider dropdown disables non-free options for Based tier
- [x] Add tier upgrade prompts when saving settings that exceed limits
- [x] Add admin bypass for testing (KW-Trader, admin, moondev)

### Frontend Fixes

- [x] Fix swarm mode locking to use correct element selector
- [x] Fix provider select ID (`ai-provider` → `main-provider-select`)
- [x] Fix token limit badge placement
- [x] Add 401 auth check in `loadTierInfo()` to prevent errors
- [x] Add CSS for locked mode-option elements
- [x] Add CSS for locked swarm-models-section

### Exchange Configuration

- [x] Confirm HYPERLIQUID as only frontend exchange option
- [x] Verify backend supports future exchanges via `EXCHANGE` constant

### Documentation

- [x] Create comprehensive README.md
- [x] Create TODO.md (this file)
- [x] Create beta-launch-todo.md

---

## In Progress

### Testing

- [ ] Live testing with real HyperLiquid account
- [ ] Test all AI providers with actual API keys
- [ ] Stress test with multiple concurrent users
- [ ] Test tier enforcement edge cases

---

## Pending - Pre-Launch

### Critical

- [ ] **Payment Integration**
  - [ ] Integrate Stripe for tier upgrades
  - [ ] Create subscription management
  - [ ] Handle payment failures gracefully

- [ ] **User Authentication**
  - [ ] Add email verification for new accounts
  - [ ] Add password reset functionality
  - [ ] Add session timeout handling

- [ ] **Security Audit**
  - [ ] Review all API endpoints for auth requirements
  - [ ] Validate all user inputs
  - [ ] Ensure API keys are never exposed in logs

### Important

- [ ] **User Onboarding**
  - [ ] Create first-time user welcome flow
  - [ ] Add tooltips for key features
  - [ ] Create quick-start guide modal

- [ ] **Error Handling**
  - [ ] Add user-friendly error messages
  - [ ] Create error recovery suggestions
  - [ ] Add retry logic for transient failures

- [ ] **Monitoring**
  - [ ] Add application metrics
  - [ ] Set up error tracking (Sentry or similar)
  - [ ] Create admin dashboard for system health

### Nice to Have

- [ ] Mobile responsive improvements
- [ ] Dark/light theme toggle
- [ ] Keyboard shortcuts
- [ ] Export trade history to CSV
- [ ] Email notifications for trades

---

## Pending - Post-Beta

### Phase 2 Features

- [ ] **Additional Exchanges**
  - [ ] Binance integration
  - [ ] Coinbase integration
  - [ ] Bybit integration

- [ ] **Backtesting Integration**
  - [ ] Connect RBI agent to dashboard
  - [ ] Display backtest results in UI
  - [ ] One-click strategy deployment

- [ ] **Strategy Marketplace**
  - [ ] User-created strategies
  - [ ] Strategy sharing
  - [ ] Performance leaderboard

- [ ] **Advanced Analytics**
  - [ ] Detailed PnL breakdown
  - [ ] Win rate statistics
  - [ ] AI decision history

- [ ] **Social Features**
  - [ ] Copy trading
  - [ ] Performance sharing
  - [ ] Community strategies

---

## Known Issues

| Issue | Severity | Status |
|-------|----------|--------|
| AI packages not installed in test env | Low | Expected - installs via requirements.txt |
| Ollama server not running locally | Low | Expected - optional feature |
| Some providers require paid API keys | Info | By design |

---

## Rate Limits Reference

| Provider | Limit | Notes |
|----------|-------|-------|
| OllamaFreeAPI | 100/hour | Free, no API key |
| Ollama (Local) | Unlimited | Requires local install |
| Gemini | 10-15 RPM | Free tier available |
| Groq | ~14,400/day | Very fast |
| DeepSeek | No hard limits | Pay per token |
| OpenAI | Varies by tier | Pay per token |
| Anthropic | Varies by tier | Pay per token |

---

## Test Accounts

For beta testing, these accounts have full admin access:

| Username | Access Level |
|----------|-------------|
| KW-Trader | Full (all tiers) |
| admin | Full (all tiers) |
| moondev | Full (all tiers) |

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| v0.9 | Jan 2026 | Pre-beta: Tier system, BYOK, OllamaFreeAPI |
| v0.8 | Dec 2025 | Dashboard UI, settings management |
| v0.7 | Nov 2025 | Swarm mode, multi-model support |

---

## Contact

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Discord:** [discord.gg/8UPuVZ53bh](https://discord.gg/8UPuVZ53bh)
- **Email:** moon@algotradecamp.com
