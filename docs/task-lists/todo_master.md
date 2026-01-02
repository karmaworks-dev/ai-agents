# Trading Bot Enhancement - Master TO-DO

**Project Overview**: Enhance existing trading bot with WebSocket data, improved trading logic, UI redesign, and agent memory system

**Total Tasks**: 4 main categories  
**Timeline**: 8-12 weeks  
**Priority Order**: Development → UI/UX → Agent Memory  

---

## 📋 Quick Reference

### Where to Find What

| Topic | Document | Section |
|-------|----------|---------|
| Bug fixes & cleanup | DEV-TASKS.md | Phase 1 |
| WebSocket integration | DEV-TASKS.md | Phase 2 |
| Trading logic fixes | DEV-TASKS.md | Phase 3 |
| Order execution | DEV-TASKS.md | Phase 4 |
| Strategy integration | DEV-TASKS.md | Phase 5 |
| Header & layout | UI-UX-TASKS.md | Phase 1-3 |
| News ticker | UI-UX-TASKS.md | Phase 1.2 |
| 3-column layout | UI-UX-TASKS.md | Phase 2 |
| Dark/light mode | UI-UX-TASKS.md | Phase 3 |
| Agent memory system | AGENT-RL.md | All phases |
| Trade history logging | AGENT-RL.md | Phase 1 |
| Thinking memory | AGENT-RL.md | Phase 2 |
| Preparation phase | AGENT-RL.md | Phase 3 |

---

## 🎯 Priority Order

### Phase 1: Critical Fixes (Week 1-2)
**Priority: HIGHEST**
- [ ] Fix duplicate logs
- [ ] Remove 🤖 emojis
- [ ] Add ♾️ emoji for SWARM logs
- [ ] Fix order of operations (CLOSE → RE-EVALUATE → OPEN)

**Why First**: These are breaking issues that affect system reliability

**Document**: DEV-TASKS.md → Phase 1

---

### Phase 2: WebSocket Foundation (Week 2-4)
**Priority: HIGH**
- [ ] Implement Hyperliquid WebSocket connection
- [ ] Real-time price data streaming
- [ ] Order book data integration
- [ ] Replace API polling with WebSocket

**Why Next**: Foundation for all other improvements (execution, UI updates)

**Document**: DEV-TASKS.md → Phase 2

---

### Phase 3: Trading Logic (Week 4-6)
**Priority: HIGH**
- [ ] Fix order of operations (CRITICAL)
- [ ] Implement smart leverage system
- [ ] Dynamic TP/SL based on confidence
- [ ] Trailing stop loss
- [ ] Limit order execution with orderbook data
- [ ] 60-second fill timeout

**Why Next**: Core trading improvements that directly impact profitability

**Document**: DEV-TASKS.md → Phase 3-4

---

### Phase 4: UI/UX Redesign (Week 6-9)
**Priority: MEDIUM**
- [ ] Sticky header (OpenRouter style)
- [ ] News ticker (CoinMarketCap API)
- [ ] 3-column layout
- [ ] Dark/light mode toggle
- [ ] Agent Insights panel (bottom right)
- [ ] Fixed footer with P&L
- [ ] Manual close buttons on positions

**Why Next**: Improves user experience and makes system easier to monitor

**Document**: UI-UX-TASKS.md → All phases

---

### Phase 5: Strategy Integration (Week 7-8)
**Priority: MEDIUM**
- [ ] Bypass strategy_agent.py (keep file, don't use)
- [ ] Load strategies from src/strategies/custom/
- [ ] Front-end strategy selector
- [ ] Direct strategy calls from trading_agent

**Why Next**: Enables flexible strategy switching

**Document**: DEV-TASKS.md → Phase 5

---

### Phase 6: Agent Memory System (Week 9-12)
**Priority: MEDIUM (Can be done in parallel with UI/UX)
- [ ] Trade memory cache (trade_memory.json)
- [ ] Thinking memory (rotating .md files)
- [ ] Two-phase cycle (Preparation → Execution)
- [ ] Agent preparation prompt (30-60s review)
- [ ] UI integration for agent insights
- [ ] Memory stats display

**Why Last**: Enhancement that improves decision-making over time

**Document**: AGENT-RL.md → All phases

---

## 📊 Task Summary by Category

### Development Tasks
- **Phase 1**: Bug Fixes (3 tasks)
- **Phase 2**: WebSocket (4 tasks)
- **Phase 3**: Trading Logic (6 tasks)
- **Phase 4**: Smart Execution (5 tasks)
- **Phase 5**: Strategy Integration (4 tasks)
- **Total**: 22 subtasks

### UI/UX Tasks
- **Phase 1**: Header & Subheader (2 tasks)
- **Phase 2**: 3-Column Layout (7 tasks)
- **Phase 3**: Theme & Branding (3 tasks)
- **Phase 4**: Interactions (2 tasks)
- **Total**: 14 subtasks

### Agent Memory Tasks
- **Phase 1**: Trade Memory (3 tasks)
- **Phase 2**: Thinking Memory (3 tasks)
- **Phase 3**: Integration (4 tasks)
- **Total**: 10 subtasks

**Grand Total**: 46 subtasks

---

## 🔥 Critical Path Items

These MUST be done before anything else:

1. **Fix Order of Operations** (DEV-TASKS Phase 3.1)
   - Currently opens positions before closing
   - Causes allocation conflicts
   - BLOCKING other trading logic improvements

2. **Accurate P&L Calculations** (DEV-TASKS Phase 3.4)
   - Must include slippage (~0.04%)
   - Must include maker/taker fees
   - Must track AI API costs per cycle
   - Agent needs to know operational costs
   - CRITICAL for proper WIN/LOSS recording

3. **WebSocket Integration** (DEV-TASKS Phase 2)
   - Required for real-time data
   - Needed for smart execution
   - Needed for UI live updates

4. **Remove Duplicate Logs** (DEV-TASKS Phase 1.1)
   - Clutters console
   - Makes debugging difficult

---

## 📁 Project File Structure

```
trading-bot/
├── src/
│   ├── agents/
│   │   ├── trading_agent.py          # Main trading logic
│   │   ├── cycle_manager.py          # Two-phase cycle (NEW)
│   │   └── strategy_agent.py         # Keep but bypass
│   ├── strategies/
│   │   └── custom/
│   │       └── example_strategy.py   # Load from here
│   ├── memory/
│   │   ├── trade_memory.json         # Trade history (NEW)
│   │   ├── thinking/                 # Rotating .md files (NEW)
│   │   ├── memory_manager.py         # Load/save (NEW)
│   │   └── thinking_manager.py       # Thinking memory (NEW)
│   ├── websocket/
│   │   ├── hyperliquid_ws.py        # WebSocket client (NEW)
│   │   └── orderbook_feed.py        # Orderbook data (NEW)
│   └── ui/
│       └── components/
│           ├── Header.tsx            # Redesigned
│           ├── NewsTicker.tsx        # CoinMarketCap feed (NEW)
│           ├── ThreeColumnLayout.tsx # New layout (NEW)
│           ├── AgentInsights.tsx     # Memory display (NEW)
│           └── Footer.tsx            # Fixed footer (NEW)
├── docs/
│   ├── DEV-TASKS.md                  # Development tasks
│   ├── UI-UX-TASKS.md                # UI/UX tasks
│   ├── AGENT-RL.md                   # Agent memory system
│   └── TO-DO.md                      # This file
└── data/
    ├── trade_memory.json             # 500 trades (~500 KB)
    └── thinking/                     # 10 rotating files (5 MB max)
        ├── thoughts_001.md
        ├── thoughts_002.md
        └── ...
```

---

## 🎨 UI/UX Design Notes

### Branding
- **Logo**: Blue/purple spiral galaxy
- **Usage**: Favicon, header icon, footer icon
- **Color Scheme**: Dark mode primary, light mode secondary
- **Accent Colors**: Blue/purple gradient (from logo)

### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│ HEADER (Sticky)                          [Dark/Light]  │
│ ├─ Logo  ├─ Models  ├─ Chat  ├─ Rankings  ├─ Docs     │
├─────────────────────────────────────────────────────────┤
│ NEWS TICKER: Scrolling feed from CoinMarketCap...      │
├─────────────────────────────────────────────────────────┤
│ LEFT (25%)    │ CENTER (45%)      │ RIGHT (30%)        │
│ Portfolio     │ Open Positions    │ Agent Status       │
│ Ticker        │ [Manual Close]    │ [RUNNING]          │
│               │                   │                    │
│ Order Book    │ Agent Console     │ Account Info       │
│ Ticker        │                   │ Wallet: 0xA8..     │
│               │ Recent Trades     │                    │
│               │                   │ Agent Settings     │
├─────────────────────────────────────────────────────────┤
│ FOOTER: Total P&L: +$1,234 (+5.6%)    🕐 14:32:15  🌀  │
└─────────────────────────────────────────────────────────┘
```

### Agent Insights Panel
**Location**: Bottom right of right column  
**Content**: 
- Recent agent preparation insights
- Current strategy summary
- Pattern observations from thinking memory
- Win rate trends

---

## 🔧 Technical Requirements

### Dependencies to Install
```bash
# WebSocket
pip install websockets

# Technical analysis (if needed)
pip install ta-lib

# For agent memory
# (No new dependencies - use built-in json/markdown)
```

### Environment Variables
```env
HYPERLIQUID_WS_URL=wss://api.hyperliquid.xyz/ws
COINMARKETCAP_API_KEY=your_key_here
```

### Storage Requirements
- Trade Memory: ~500 KB
- Thinking Memory: ~5 MB
- Total: ~5.5 MB additional storage

---

## 🧪 Testing Checklist

### Development
- [ ] WebSocket connects and stays connected
- [ ] Order book data updates in real-time
- [ ] Positions close before opening new ones
- [ ] Limit orders fill within 60 seconds
- [ ] Smart leverage calculates correctly
- [ ] Trailing stop loss updates properly
- [ ] Strategies load from custom folder

### UI/UX
- [ ] Header stays sticky on scroll
- [ ] News ticker scrolls smoothly
- [ ] Dark/light mode toggle works
- [ ] 3-column layout responsive
- [ ] Manual close buttons work
- [ ] Footer shows correct P&L
- [ ] Agent insights update in real-time

### Agent Memory
- [ ] Trade memory logs correctly
- [ ] Thinking memory rotates at 5 MB
- [ ] Agent reviews history for 30-60s
- [ ] Preparation phase completes
- [ ] Insights display in UI
- [ ] Memory persists across restarts

---

## 📈 Success Metrics

### System Performance
- [ ] No duplicate logs
- [ ] WebSocket uptime > 99%
- [ ] Order fill rate > 70% (limit orders)
- [ ] Average slippage < 0.05%

### Trading Performance
- [ ] Positions close before opening (100% of time)
- [ ] Smart leverage working correctly
- [ ] TP/SL hit rates improved
- [ ] Win rate increase after memory system

### User Experience
- [ ] UI loads in < 3 seconds
- [ ] Real-time updates lag < 500ms
- [ ] Theme switching smooth
- [ ] All panels functional

---

## 🚀 Getting Started

### Week 1: Critical Fixes
1. Read DEV-TASKS.md Phase 1
2. Fix duplicate logs
3. Update emoji usage
4. Test log cleanup

### Week 2: WebSocket Setup
1. Read DEV-TASKS.md Phase 2
2. Set up WebSocket connection
3. Test real-time data flow
4. Replace API calls

### Week 3-4: Trading Logic
1. Read DEV-TASKS.md Phase 3-4
2. Fix order of operations
3. Implement smart leverage
4. Test execution improvements

### Week 5-6: Parallel Work
**Developer 1**: UI/UX redesign (UI-UX-TASKS.md)
**Developer 2**: Strategy integration (DEV-TASKS.md Phase 5)

### Week 7-8: Agent Memory
1. Read AGENT-RL.md
2. Implement trade memory
3. Implement thinking memory
4. Test two-phase cycle

### Week 9-10: Integration & Testing
1. Connect all components
2. Full system testing
3. Bug fixes
4. Performance optimization

### Week 11-12: Polish & Deploy
1. Final UI polish
2. Documentation
3. User testing
4. Production deployment

---

## 📝 Notes & Decisions

### Design Decisions
- **Two-phase cycle**: Gives agent time to learn from history
- **Rotating thinking memory**: Prevents unlimited growth
- **Markdown format**: Human-readable, easy to debug
- **Separate preparation**: Agent forms strategy before seeing prices

### Technical Decisions
- **WebSocket over polling**: Reduced latency, fewer API calls
- **Limit orders**: Save fees, better execution
- **Smart leverage**: Based on confidence + market conditions
- **Order of operations fix**: Prevents allocation conflicts

### UI Decisions
- **OpenRouter style**: Modern, clean, professional
- **3-column layout**: Information density + readability
- **Dark mode default**: Easier on eyes for trading
- **Fixed footer**: Always visible P&L

---

## 🐛 Known Issues to Address

1. **Duplicate logs** - Fixed in Phase 1
2. **Robot emojis everywhere** - Remove in Phase 1
3. **Opens before closing** - CRITICAL, fix in Phase 3
4. **No real-time data** - Add WebSocket in Phase 2
5. **API rate limiting** - Reduce calls via WebSocket
6. **No manual close** - Add buttons in UI Phase 2

---

## 📞 Support & Resources

### Documentation Links
- Hyperliquid API: https://hyperliquid.gitbook.io
- CoinMarketCap API: https://coinmarketcap.com/api/documentation/v1/
- OpenRouter Design: https://openrouter.ai (for reference)

### Code References
- WebSocket example: DEV-TASKS.md Phase 2
- Memory system: AGENT-RL.md Phase 1-2
- UI components: UI-UX-TASKS.md Phase 2

---

## ✅ Quick Start Checklist

**Before starting any work:**
- [ ] Read this TO-DO.md completely
- [ ] Review relevant task document (DEV/UI/AGENT)
- [ ] Check file structure section
- [ ] Note dependencies needed
- [ ] Understand priority order

**For each task:**
- [ ] Read task description
- [ ] Check for dependencies (what must be done first)
- [ ] Implement solution
- [ ] Test thoroughly
- [ ] Update documentation
- [ ] Mark task as complete

**Before moving to next phase:**
- [ ] All tasks in current phase complete
- [ ] Tests passing
- [ ] No regressions
- [ ] Documentation updated

---

## 🎯 Final Goal

A production-ready trading bot with:
- ✅ Real-time WebSocket data
- ✅ Intelligent order execution
- ✅ Smart risk management
- ✅ Beautiful, functional UI
- ✅ Agent that learns from experience
- ✅ Clean, maintainable codebase

**Target**: Fully operational system in 10-12 weeks