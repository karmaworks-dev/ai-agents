# Agent Memory System (Simplified RL)

**Concept**: Agent learns from past trades through memory review  
**Approach**: Two-phase cycle with preparation time  
**Storage**: ~6 MB total (trade memory + thinking memory)  
**Timeline**: 2-3 weeks  

---

## Overview

Instead of complex neural networks, give the agent:
1. **Trade Memory**: Objective record of wins/losses
2. **Thinking Memory**: Agent's own insights and observations
3. **Preparation Time**: 30-60 seconds to review and strategize

The LLM agent naturally learns from context - no training required!

---

## Trading Cycle Flow

```
┌─────────────────────────────────────────────────────────┐
│ PHASE 1: PREPARATION (30-60 seconds)                    │
├─────────────────────────────────────────────────────────┤
│ 1. Init                                                  │
│ 2. Get Volume Data                                       │
│ 3. Load Past 500 Trades → Agent Reviews                 │
│ 4. Load Thinking Memory → Agent Reviews                 │
│ 5. Agent: "Think and Prepare" (analyze patterns)        │
│    → What worked? What didn't?                           │
│    → Review past insights and observations               │
│    → Build strategy for next trades                      │
│    → Log new insights to thinking memory                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTION (normal speed)                       │
├─────────────────────────────────────────────────────────┤
│ 6. Get Current Market Data                              │
│ 7. Trade Decision Prompt (informed by preparation)      │
│ 8. Execute Trade                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Two Memory Systems

### 1. Trade Memory (trade_memory.json)
**Purpose**: Objective record of all trades  
**Format**: JSON  
**Size**: ~500 KB (500 trades)  
**Retention**: Last 500 trades  

**Structure**:
```json
{
  "trades": [
    {
      "timestamp": "2025-01-02T10:30:00Z",
      "token": "BTC",
      "direction": "LONG",
      "result": "+5.2%",
      "entry": 95000,
      "exit": 99940,
      "confidence": 0.85
    }
  ],
  "summary": {
    "total_trades": 47,
    "wins": 28,
    "losses": 19,
    "win_rate": "59.6%",
    "avg_win": "+4.3%",
    "avg_loss": "-2.1%"
  }
}
```

---

### 2. Thinking Memory (rotating .md files)
**Purpose**: Agent's subjective insights  
**Format**: Markdown  
**Size**: Max 5 MB (10 rotating files)  
**Retention**: Auto-rotate when full  

**Structure**:
```
data/thinking/
├── thoughts_001.md  (~500 KB)
├── thoughts_002.md
├── thoughts_003.md
├── ...
└── thoughts_010.md
```

**Content Example**:
```markdown
# 2025-01-02 09:00 - Morning Preparation

## Pattern Observed
BTC LONG trades with confidence >0.8 and volume >2B:
- Win rate: 78% (14 wins, 4 losses)
- Average win: +5.8%
- Average loss: -1.9%

## Hypothesis
High volume indicates strong trend continuation.
High confidence correlates with clearer signals.

## Strategy for Today
1. Prioritize BTC LONG when both conditions met
2. Increase position size on high confidence
3. Use tighter stop loss (-1.5%) due to strong trend

## Avoid
- ETH SHORT positions (only 35% win rate lately)
- Low confidence trades (<0.6) in choppy markets

---

# 2025-01-02 12:00 - Midday Review

## Results So Far
- Opened 3 BTC LONG positions
- All 3 profitable: +4.2%, +6.1%, +3.8%
- Pattern confirmed ✅

## Adjustment
Continue current strategy. Market showing strong momentum.

---

# 2025-01-02 15:00 - Afternoon Session

## New Observation
Volume dropped below 1.5B at 14:30
- Next 2 trades: 1 win, 1 loss
- Pattern breaks in low volume

## Updated Strategy
Only take trades when volume >2B
Reduce position size if volume declining
```

---

## Phase 1: Trade Memory (Week 1)

### 1.1 Create Memory Storage
**File**: `data/trade_memory.json`

**Implementation**:
```python
def init_trade_memory():
    memory = {
        "trades": [],
        "summary": {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": "0%",
            "avg_win": "+0.0%",
            "avg_loss": "0.0%"
        }
    }
    save_memory(memory)
```

**Files**:
- `src/memory/memory_manager.py`
- `data/trade_memory.json`

---

### 1.2 Log Trade Results
**When**: After position closes

```python
def log_trade_result(trade_data):
    # Calculate profit % (including fees and slippage)
    gross_profit = calculate_gross_profit(trade_data)
    
    # Subtract realistic costs
    slippage = 0.04  # 0.04% average
    entry_fee = get_fee(trade_data.entry_order_type)  # 0.03% taker or -0.01% maker
    exit_fee = get_fee(trade_data.exit_order_type)
    
    net_profit_pct = gross_profit - slippage - entry_fee - exit_fee
    
    result = f"+{net_profit_pct:.1f}%" if net_profit_pct > 0 else f"{net_profit_pct:.1f}%"
    
    # Create record
    record = {
        "timestamp": now(),
        "token": trade_data.token,
        "direction": trade_data.direction,
        "result": result,
        "entry": trade_data.entry_price,
        "exit": trade_data.exit_price,
        "confidence": trade_data.confidence,
        "fees": entry_fee + exit_fee,
        "slippage": slippage
    }
    
    # Append and save
    memory = load_memory()
    memory["trades"].append(record)
    
    # Keep last 500
    if len(memory["trades"]) > 500:
        memory["trades"] = memory["trades"][-500:]
    
    update_summary(memory)
    save_memory(memory)
```

---

### 1.3 Track Operational Costs
**Goal**: Agent aware of its running costs  
**Why**: Creates intrinsic motivation to be profitable

```python
def track_cycle_economics(tokens_used, trades):
    # Calculate AI API cost
    cost_per_million = 3.00  # Claude Sonnet pricing
    api_cost = (tokens_used / 1_000_000) * cost_per_million
    
    # Calculate total P&L (net of fees)
    total_pnl = sum(trade.net_profit for trade in trades)
    
    # Net profit after operational costs
    net_profit = total_pnl - api_cost
    
    return {
        "api_cost": api_cost,
        "tokens_used": tokens_used,
        "gross_pnl": total_pnl,
        "net_pnl": net_profit,
        "profitable_cycle": net_profit > 0,
        "break_even_pnl": api_cost  # Must win at least this much
    }
```

**Include in Trade Memory**:
```json
{
  "trades": [...],
  "summary": {...},
  "cycle_economics": {
    "last_cycle_api_cost": 0.032,
    "last_cycle_tokens": 10654,
    "last_cycle_net_pnl": 1.25,
    "profitable": true
  }
}
```

---

### 1.4 Memory Statistics
**Calculate**: Summary stats from trade history

```python
def update_summary(memory):
    trades = memory["trades"]
    wins = [t for t in trades if t["result"].startswith("+")]
    losses = [t for t in trades if not t["result"].startswith("+")]
    
    memory["summary"] = {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": f"{len(wins)/len(trades)*100:.1f}%",
        "avg_win": calculate_avg(wins),
        "avg_loss": calculate_avg(losses)
    }
```

---

## Phase 2: Thinking Memory (Week 2)

### 2.1 Create Thinking Storage
**Directory**: `data/thinking/`  
**Files**: `thoughts_001.md` through `thoughts_010.md`

```python
def init_thinking_memory():
    Path("data/thinking").mkdir(exist_ok=True)
    
    # Create first file
    thinking_file = Path("data/thinking/thoughts_001.md")
    thinking_file.write_text("# Agent Thinking Memory\n\n")
```

---

### 2.2 Append Agent Insights
**When**: After preparation phase

```python
def append_thinking(insights):
    # Find current active file
    files = sorted(Path("data/thinking").glob("thoughts_*.md"))
    current = files[-1]
    
    # Check size
    if current.stat().st_size > 500_000:  # 500 KB
        current = create_next_file(files)
    
    # Append insights
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n\n# {timestamp}\n\n{insights}\n\n---\n"
    
    with open(current, 'a') as f:
        f.write(entry)
```

---

### 2.3 File Rotation
**When**: Total size exceeds 5 MB

```python
def rotate_thinking_files():
    files = sorted(Path("data/thinking").glob("thoughts_*.md"))
    total_size = sum(f.stat().st_size for f in files)
    
    if total_size > 5_000_000:  # 5 MB
        # Delete oldest file
        oldest = files[0]
        oldest.unlink()
        logger.info(f"Rotated thinking memory: deleted {oldest.name}")
    
    # Renumber if needed
    if len(files) < 10:
        # Create new file for next insights
        next_num = len(files) + 1
        new_file = Path(f"data/thinking/thoughts_{next_num:03d}.md")
        new_file.touch()
```

---

### 2.4 Load All Thinking Memory
**When**: During preparation phase

```python
def load_thinking_memory():
    files = sorted(Path("data/thinking").glob("thoughts_*.md"))
    
    all_thoughts = ""
    for file in files:
        all_thoughts += file.read_text() + "\n\n"
    
    return all_thoughts
```

---

## Phase 3: Two-Phase Cycle Integration (Week 3)

### 3.1 Preparation Phase
**Duration**: 30-60 seconds  
**Goal**: Agent reviews history and prepares strategy

```python
async def preparation_phase():
    print("📚 PHASE 1: PREPARATION")
    
    # 1. Init
    print("[PREP] Initializing...")
    
    # 2. Get Volume
    volume = await get_volume_data()
    
    # 3. Load Trade Memory
    trade_memory = load_trade_memory()
    print(f"[PREP] Loaded {len(trade_memory['trades'])} trades")
    
    # 4. Load Thinking Memory
    thinking_memory = load_thinking_memory()
    print(f"[PREP] Loaded {len(thinking_memory)} chars of thoughts")
    
    # 5. Agent Preparation Prompt
    prep_prompt = f"""
You are preparing for the next trading cycle.

**Your Past 500 Trades:**
{json.dumps(trade_memory, indent=2)}

**Your Past Insights & Observations:**
{thinking_memory}

**Current Volume Data:**
{volume}

**Your Operational Costs:**
Last cycle you used {trade_memory['cycle_economics']['last_cycle_tokens']:,} tokens
API cost: ${trade_memory['cycle_economics']['last_cycle_api_cost']:.4f}
You made ${trade_memory['cycle_economics']['last_cycle_net_pnl']:.2f} net profit

⚠️ Remember: You cost money to run!
- Every cycle costs ~$0.03 in AI API fees
- You need to WIN to justify your existence
- Target: Make 10x your cost per cycle ($0.30+)
- Quality over quantity - avoid unprofitable trades

**Instructions:**
Take 30-60 seconds to:
1. Review what worked and what didn't
2. Identify patterns in your trading history
3. Review your past insights
4. Develop a strategy for upcoming trades
5. Consider: Are you being profitable enough to cover costs?

Think deeply about:
- When did you win? What conditions?
- When did you lose? What went wrong?
- What patterns do you see?
- What insights from your thinking memory are still relevant?
- What new observations can you make?
- How can you be MORE profitable?

**Provide:**
1. Your analysis of patterns
2. Your strategy for today
3. New insights to remember
"""
    
    # Get agent analysis (30-60 seconds)
    insights = await agent.analyze(prep_prompt)
    
    # Save insights to thinking memory
    append_thinking(insights)
    
    print(f"[PREP] Complete. Strategy prepared.")
    
    return {
        "insights": insights,
        "volume": volume,
        "summary": trade_memory["summary"]
    }
```

---

### 3.2 Execution Phase
**Duration**: Normal speed  
**Goal**: Make trading decisions using preparation

```python
async def execution_phase(preparation):
    print("⚡ PHASE 2: EXECUTION")
    
    # 6. Get Market Data
    market = await get_current_market_data()
    
    # 7. Trade Decision Prompt
    trade_prompt = f"""
You are making trading decisions for this cycle.

**Your Prepared Strategy:**
{preparation["insights"]}

**Your Track Record:**
- Win Rate: {preparation["summary"]["win_rate"]}
- Average Win: {preparation["summary"]["avg_win"]}
- Average Loss: {preparation["summary"]["avg_loss"]}

**Current Market:**
{market}

**Decision:**
Based on your preparation and current conditions, should you trade?
- Token: ?
- Direction: LONG/SHORT?
- Confidence: 0.0-1.0
- Reasoning: Why?

Remember your preparation insights and apply them.
"""
    
    # Get decision
    decision = await agent.decide(trade_prompt)
    
    return decision
```

---

### 3.3 Complete Cycle
**Orchestration**: Run both phases in sequence

```python
async def trading_cycle():
    cycle_start = time.time()
    
    print("="*60)
    print("🔄 NEW TRADING CYCLE")
    print("="*60)
    
    # Phase 1: Preparation (30-60s)
    prep_start = time.time()
    preparation = await preparation_phase()
    prep_time = time.time() - prep_start
    print(f"[TIMING] Preparation: {prep_time:.1f}s")
    
    # Phase 2: Execution
    exec_start = time.time()
    decision = await execution_phase(preparation)
    exec_time = time.time() - exec_start
    print(f"[TIMING] Execution: {exec_time:.1f}s")
    
    # Execute trade
    if decision.should_trade:
        result = await execute_trade(decision)
        await log_trade_result(result)
    
    print(f"[TIMING] Total: {time.time() - cycle_start:.1f}s")
    print("="*60)
```

---

## Phase 4: UI Integration (Week 3)

### 4.1 Agent Insights Button
**Location**: Bottom right of right column  
**Purpose**: Opens modal to view agent's thinking

**Component**:
```jsx
function AgentInsightsButton({ lastUpdate }) {
  const [modalOpen, setModalOpen] = useState(false);
  
  return (
    <>
      <Button 
        onClick={() => setModalOpen(true)}
        className="agent-insights-btn"
      >
        🧠 Agent Insights
        <SubText>Last updated: {lastUpdate}</SubText>
      </Button>
      
      {modalOpen && (
        <AgentInsightsModal 
          onClose={() => setModalOpen(false)} 
        />
      )}
    </>
  );
}
```

**Files**:
- `src/ui/components/AgentInsightsButton.tsx`

---

### 4.2 Agent Insights Modal
**Display**: Full-screen modal with agent memory  
**Sections**:
1. Performance summary
2. Recent preparation insights
3. Scrollable thinking memory viewer
4. Action buttons (Clear, Export, Close)

**Component**:
```jsx
function AgentInsightsModal({ onClose }) {
  const [memory, setMemory] = useState(null);
  
  useEffect(() => {
    loadMemory();
  }, []);
  
  const loadMemory = async () => {
    const tradeMemory = await api.get('/memory/trades');
    const thinkingMemory = await api.get('/memory/thinking');
    setMemory({ trade: tradeMemory, thinking: thinkingMemory });
  };
  
  const clearMemory = async () => {
    if (confirm("Clear all agent thinking memory?")) {
      await api.delete('/memory/thinking');
      toast.success("Memory cleared");
      onClose();
    }
  };
  
  return (
    <Modal onClose={onClose}>
      <ModalHeader>
        🧠 Agent Memory & Insights
        <CloseButton onClick={onClose}>✕</CloseButton>
      </ModalHeader>
      
      <ModalBody>
        {/* Performance Summary */}
        <Section title="📊 Performance Summary">
          <StatGrid>
            <Stat label="Win Rate" value={memory.trade.summary.win_rate} />
            <Stat label="Total Trades" value={memory.trade.summary.total_trades} />
            <Stat label="Avg Win" value={memory.trade.summary.avg_win} color="green" />
            <Stat label="Avg Loss" value={memory.trade.summary.avg_loss} color="red" />
          </StatGrid>
        </Section>
        
        {/* Recent Preparation */}
        <Section title="📚 Recent Preparation">
          <PreparationInsights>
            {memory.recentPreparation}
          </PreparationInsights>
        </Section>
        
        {/* Scrollable Thinking Memory */}
        <Section title="📝 Thinking Memory">
          <ScrollableMemory>
            <MarkdownViewer content={memory.thinking} />
          </ScrollableMemory>
        </Section>
      </ModalBody>
      
      <ModalFooter>
        <Button onClick={clearMemory} variant="danger">
          🗑️ Clear Memory
        </Button>
        <Button onClick={exportMemory}>
          📥 Export
        </Button>
        <Button onClick={onClose}>
          Close
        </Button>
      </ModalFooter>
    </Modal>
  );
}
```

**Scrollable Memory Styling**:
```css
.scrollable-memory {
  height: 400px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  background: var(--bg-tertiary);
}

.scrollable-memory::-webkit-scrollbar {
  width: 8px;
}

.scrollable-memory::-webkit-scrollbar-thumb {
  background: var(--accent-color);
  border-radius: 4px;
}
```

**Files**:
- `src/ui/components/AgentInsightsModal.tsx`
- `src/ui/components/MemoryViewer.tsx`
- `src/ui/styles/modal.css`

---

### 4.3 Clear Memory API Endpoint
**Backend**: API to delete thinking memory

```python
@app.delete("/api/memory/thinking")
async def clear_thinking_memory():
    """Delete all thinking memory files"""
    thinking_dir = Path("data/thinking")
    
    # Delete all markdown files
    for file in thinking_dir.glob("thoughts_*.md"):
        file.unlink()
    
    # Create fresh first file
    init_thinking_memory()
    
    return {
        "success": True,
        "message": "Thinking memory cleared",
        "files_deleted": len(list(thinking_dir.glob("thoughts_*.md")))
    }

@app.get("/api/memory/thinking")
async def get_thinking_memory():
    """Get all thinking memory content"""
    thinking = load_thinking_memory()
    
    return {
        "content": thinking,
        "size_mb": len(thinking) / (1024 * 1024),
        "files": len(list(Path("data/thinking").glob("thoughts_*.md")))
    }
```

**Files**:
- `src/api/memory_routes.py`

---

### 4.4 Preparation Status Display
**Display**: Show when agent is reviewing

```jsx
function PreparationStatus({ isActive, progress }) {
  if (!isActive) return null;
  
  return (
    <StatusBar>
      🧠 Agent reviewing 500 trades and past insights...
      <ProgressBar value={progress} max={60} />
      <Timer>{60 - progress}s remaining</Timer>
    </StatusBar>
  );
}
```

---

### 4.3 Memory Stats Display
**Location**: Agent Settings panel

```jsx
function MemoryStats({ memory }) {
  return (
    <StatsGrid>
      <Stat label="Trades Logged" value={memory.total_trades} />
      <Stat label="Memory Size" value={memory.disk_usage} />
      <Stat label="Thinking Files" value={memory.thinking_files} />
      <Stat label="Oldest Trade" value={memory.oldest_date} />
    </StatsGrid>
  );
}
```

---

## File Structure

```
trading-bot/
├── src/
│   ├── memory/
│   │   ├── memory_manager.py      # Trade memory load/save
│   │   └── thinking_manager.py    # Thinking memory management
│   ├── agents/
│   │   └── cycle_manager.py       # Two-phase cycle
│   └── ui/
│       └── components/
│           └── AgentInsights.tsx  # Display insights
├── data/
│   ├── trade_memory.json          # 500 trades (~500 KB)
│   └── thinking/                  # Rotating memory (5 MB max)
│       ├── thoughts_001.md
│       ├── thoughts_002.md
│       └── ...
```

---

## Storage Budget

| Component | Size | Notes |
|-----------|------|-------|
| Trade Memory | ~500 KB | 500 trades x 1 KB |
| Thinking Memory | ~5 MB | 10 files rotating |
| **Total** | **~5.5 MB** | ✅ Minimal footprint |

---

## Benefits

✅ **Simple**: No neural networks or training  
✅ **Transparent**: Human-readable memory files  
✅ **Immediate**: Works from day one  
✅ **Natural Learning**: Agent learns from context  
✅ **Self-Aware**: Agent knows its own history  
✅ **Minimal Storage**: Only ~6 MB  
✅ **Debuggable**: Easy to inspect memory  

---

## Example Agent Learning

**Day 1 - First trades**
```markdown
# Morning Session
Opened BTC LONG (confidence 0.75): +3.2% ✅
Opened ETH SHORT (confidence 0.65): -1.8% ❌

Observation: BTC LONG worked well. ETH SHORT didn't.
```

**Day 2 - Learning from Day 1**
```markdown
# Morning Preparation
Reviewing yesterday: BTC LONG was profitable.
Strategy today: Focus on BTC LONG, avoid ETH SHORT.

# Results
BTC LONG: +4.5% ✅
BTC LONG: +5.8% ✅
Pattern confirmed!
```

**Day 3 - Refining strategy**
```markdown
# Preparation
After 3 days: BTC LONG has 80% win rate when confidence >0.75
New insight: Only take BTC LONG with high confidence

# Strategy
- BTC LONG only if confidence >0.75
- Increase position size on high confidence
- Tighter stop loss due to strong pattern
```

The agent naturally develops expertise over time!

---

## Testing Checklist

- [ ] Trade memory logs correctly on close
- [ ] Thinking memory appends new insights
- [ ] Files rotate at 5 MB limit
- [ ] Agent gets 30-60s preparation time
- [ ] Preparation insights save to thinking memory
- [ ] UI shows agent insights
- [ ] Memory persists across restarts
- [ ] No memory leaks or unlimited growth

---

## Implementation Priority

**Week 1**: Trade memory system  
**Week 2**: Thinking memory + rotation  
**Week 3**: Two-phase cycle integration + UI  

---

## Notes

### Why This Works
The LLM is already good at pattern recognition. By giving it:
1. **Concrete data** (trade results)
2. **Its own past thoughts** (thinking memory)
3. **Time to reflect** (30-60s preparation)

It naturally learns and improves without any training!

### Thinking Memory Format
Markdown allows agent to:
- Structure observations clearly
- Write hypotheses
- Track strategy evolution
- Review past insights easily

Human-readable = easier debugging!

### Rotation Strategy
10 files x 500 KB = 5 MB cap
Oldest files deleted first
Agent always has access to recent insights

This is like a trader's journal - reviewed before each session! 📓🧠