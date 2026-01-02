# UI/UX Design Tasks

**Focus**: Interface redesign, user experience, visual improvements  
**Timeline**: 3-4 weeks  
**Priority**: Start after WebSocket integration  

---

## Phase 1: Header & Subheader (Week 1)

### 1.1 Sticky Header Redesign
**Goal**: Modern, professional header inspired by OpenRouter  
**Requirements**:
- Sticky positioning (stays at top on scroll)
- Clean, minimal design
- Logo on left, navigation center, theme toggle on right
- Smooth animations

**Structure**:
```
┌─────────────────────────────────────────────┐
│ 🌀 Logo   Models  Chat  Rankings  Docs [☀️/🌙] │
└─────────────────────────────────────────────┘
```

**Styling**:
- Height: 60px
- Background: Dark mode - `#1a1a1a`, Light mode - `#ffffff`
- Border bottom: 1px subtle
- Z-index: 1000 (always on top)

**Files**:
- `src/ui/components/Header.tsx`
- `src/ui/styles/header.css`

---

### 1.2 News Ticker Subheader
**Goal**: Scrolling news feed from CoinMarketCap  
**Requirements**:
- Height: 16px line
- Font size: 12px
- Auto-scrolling animation
- Shows trending data + headlines

**Data Source**: CoinMarketCap Free API
- Endpoint: `/v1/cryptocurrency/trending/latest`
- Endpoint: `/v1/content/latest`

**Example Content**:
```
BTC +2.3% ($96,234) | ETH +1.8% ($3,521) | Breaking: SEC approves Bitcoin ETF... 
```

**Animation**:
```css
@keyframes scroll {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}
```

**Files**:
- `src/ui/components/NewsTicker.tsx`
- `src/services/coinmarketcap_api.ts`

---

## Phase 2: Three-Column Layout (Week 2)

### 2.1 Layout Structure
**Goal**: Responsive 3-column dashboard  
**Column Widths**:
- Left: 25%
- Center: 45%
- Right: 30%

**Responsive**:
- Desktop (>1920px): 3 columns
- Tablet (768-1920px): 3 columns (adjusted widths)
- Mobile (<768px): Stacked single column

**Files**:
- `src/ui/components/ThreeColumnLayout.tsx`

---

### 2.2 Left Column Components

**Top: Portfolio Ticker**
- Display current equity value
- Update in real-time
- Large, readable font
- Color-coded (green if positive, red if negative)

**Bottom: Order Book Ticker**
- Show top 5 bids and asks
- Real-time updates from WebSocket
- Price + volume display
- Highlight spread

**Example**:
```
Portfolio Equity: $10,234.56 (+5.2%)

Order Book (BTC)
Asks:
  96215  0.8
  96210  1.2
──────────────
  96205  [SPREAD]
──────────────
Bids:
  96200  1.5
  96195  2.1
```

**Files**:
- `src/ui/components/PortfolioTicker.tsx`
- `src/ui/components/OrderBookTicker.tsx`

---

### 2.3 Center Column Components

**Top: Open Positions List**
- Table format with columns:
  - Symbol
  - Side (LONG/SHORT) - color coded
  - Size
  - Entry Price
  - Mark Price
  - P&L ($)
  - P&L (%)
  - [Close] button

**Manual Close Button**:
- Red button on each row
- Confirmation dialog
- Instant position close

**Bottom Left: Agent Console**
- Scrollable log window
- Color-coded log levels
- Auto-scroll to bottom
- Search/filter functionality

**Bottom Right: Recent Trades**
- Compact format:
  - Symbol
  - Leverage (e.g., 5x)
  - % P&L
  - $ P&L
- Last 20 trades
- Color-coded wins/losses

**Files**:
- `src/ui/components/OpenPositions.tsx`
- `src/ui/components/AgentConsole.tsx`
- `src/ui/components/RecentTrades.tsx`

---

### 2.4 Right Column Components

**Agent Status Badge** (Top Right)
- Visual indicator: RUNNING / STAND BY / READY
- Color coded:
  - RUNNING: Green with pulse animation
  - STAND BY: Yellow
  - READY: Blue
- Large, visible badge

**Account Information Panel**
- **User Info**:
  - Wallet address: `0xA871...8078` [Copy]
  - Username
  - Current plan (Pro, Free, etc.)

- **Account Metrics**:
  - Spot Balance: $X,XXX.XX
  - Perps Balance: $X,XXX.XX
  - Unrealized PNL: $XXX.XX (color coded)
  - Cross Margin Ratio: XX.X%
  - Maintenance Margin: $XXX.XX
  - Account Leverage: X.Xx

**Agent Settings Panel**
- Display current settings:
  - Monitored Tokens: BTC, ETH, SOL
  - Timeframe: 15m
  - Strategy: Example Strategy
  - Confidence Threshold: 0.7
  - Cycle Minutes: 15
- Edit button for quick access

**Agent Insights Panel** (Bottom Right)
- Display recent preparation insights
- Show pattern observations
- Current strategy summary
- Win rate trends
- Scrollable, last 5 insights

**Example**:
```
📚 Last Preparation (2m ago)
"BTC LONG trades with confidence >0.8 have 
72% win rate. Focusing on high-confidence 
BTC opportunities today."

📊 Current Strategy
• Prefer BTC LONG positions
• Avoid ETH SHORT (low win rate)
• Only trade when confidence >0.7

📈 Performance
Win Rate: 59.6% (28W / 19L)
```

**Files**:
- `src/ui/components/AgentStatus.tsx`
- `src/ui/components/AccountInfo.tsx`
- `src/ui/components/AgentSettings.tsx`
- `src/ui/components/AgentInsights.tsx` ⭐

---

## Phase 3: Theme & Branding (Week 3)

### 3.1 Dark Mode (Default)
**Color Palette**:
- Background Primary: `#0a0a0a`
- Background Secondary: `#1a1a1a`
- Background Tertiary: `#2a2a2a`
- Text Primary: `#ffffff`
- Text Secondary: `#a0a0a0`
- Border: `#333333`
- Accent: Blue/purple gradient `#4a90e2` to `#8e44ad`
- Success: `#00ff88`
- Error: `#ff4444`
- Warning: `#ffaa00`

---

### 3.2 Light Mode
**Color Palette**:
- Background Primary: `#ffffff`
- Background Secondary: `#f5f5f5`
- Background Tertiary: `#eeeeee`
- Text Primary: `#1a1a1a`
- Text Secondary: `#666666`
- Border: `#dddddd`
- Accent: Same blue/purple gradient
- Success: `#00cc66`
- Error: `#cc0000`
- Warning: `#ff8800`

---

### 3.3 Theme Toggle Implementation
**UI Element**:
- Switch in header (top right)
- Icons: **⬤** (light mode) / **⏾** (dark mode)
- Smooth transition (300ms)
- Persist preference in localStorage

**Implementation**:
```tsx
const [theme, setTheme] = useState('dark');

const toggleTheme = () => {
  const newTheme = theme === 'dark' ? 'light' : 'dark';
  setTheme(newTheme);
  localStorage.setItem('theme', newTheme);
  document.documentElement.setAttribute('data-theme', newTheme);
};
```

**Files**:
- `src/ui/components/ThemeToggle.tsx`
- `src/ui/styles/themes.css`

---

### 3.4 Branding Assets
**Logo Usage**:
- Spiral galaxy logo (blue/purple gradient)
- Locations:
  - Favicon (16x16, 32x32)
  - Header icon (40x40)
  - Footer icon (24x24)
  - Loading spinner (use rotation animation)

**Logo Files Needed**:
- `public/favicon.ico`
- `public/logo-192.png`
- `public/logo-512.png`
- `src/assets/logo.svg`

**Files**:
- `src/ui/components/Logo.tsx`

---

## Phase 4: Footer & Interactions (Week 3-4)

### 4.1 Fixed Footer
**Goal**: Always-visible footer with key metrics  
**Structure**:
```
┌────────────────────────────────────────────┐
│ Total P&L: $1,234 (+5.6%)     14:32:15  🌀  │
└────────────────────────────────────────────┘
```

**Left Side**:
- Total P&L Value ($ format)
- Total P&L Percentage
- Color coded (green/red)
- Real-time updates

**Right Side**:
- System time (HH:MM:SS)
- Logo icon

**Styling**:
- Height: 40px
- Fixed to bottom (position: fixed)
- Z-index: 999
- Separator line at top

**Files**:
- `src/ui/components/Footer.tsx`

---

### 4.2 Animation & Micro-interactions
**Goal**: Smooth, polished interactions  
**Elements**:
- Button hover effects
- Status badge pulse (when running)
- Loading states
- Success/error feedback
- Smooth transitions (300ms)

**Examples**:
```css
/* Button hover */
.button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

/* Pulse animation */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
```

---

### 4.3 Agent Insights Modal ⭐⭐⭐
**Trigger**: Click "🧠 Agent Insights" button in bottom right  
**Goal**: Full-screen modal showing agent's thinking memory

**Modal Structure**:
```
┌────────────────────────────────────────────┐
│ 🧠 Agent Memory & Insights            [✕]  │
├────────────────────────────────────────────┤
│                                             │
│ 📊 Performance Summary                     │
│ ├─ Win Rate: 59.6% (28W / 19L)            │
│ ├─ Avg Win: +4.3%                          │
│ ├─ Avg Loss: -2.1%                         │
│ └─ Total Trades: 47                        │
│                                             │
│ ───────────────────────────────────────    │
│                                             │
│ 📚 Recent Preparation (2m ago)             │
│ "After reviewing 500 trades, BTC LONG      │
│ positions with confidence >0.8 show 72%    │
│ win rate. Focusing on these today."        │
│                                             │
│ 📊 Active Strategy                         │
│ • Prefer BTC LONG positions                │
│ • Avoid low confidence (<0.6) trades       │
│ • Target +5% TP, -2% SL                    │
│                                             │
│ ───────────────────────────────────────    │
│                                             │
│ 📝 Thinking Memory (scrollable ↓)          │
│ ┌─────────────────────────────────────┐   │
│ │ # 2025-01-02 15:00                   │   │
│ │                                       │   │
│ │ ## Pattern Observed                  │   │
│ │ High volume + neutral RSI = strong   │   │
│ │ trend continuation                   │   │
│ │                                       │   │
│ │ ## Strategy Update                   │   │
│ │ Focus on BTC LONG in these conditions│   │
│ │                                       │   │
│ │ ---                                  │   │
│ │                                       │   │
│ │ # 2025-01-02 12:00                   │   │
│ │ ...                                  │ ↓ │
│ │ (scrollable to older entries)        │   │
│ └─────────────────────────────────────┘   │
│                                             │
│ [🗑️ Clear Memory] [📥 Export]  [Close]    │
└────────────────────────────────────────────┘
```

**Features**:

1. **Performance Summary** (Top)
   - Key stats at a glance
   - Real-time updates

2. **Recent Preparation** (Middle)
   - Last agent preparation insights
   - Current active strategy
   - Easy to read format

3. **Thinking Memory Viewer** (Bottom - Scrollable)
   - Display all thinking memory markdown files
   - Newest entries at top
   - Scroll down to see older entries
   - Formatted markdown rendering
   - Syntax highlighting for code blocks

4. **Action Buttons** (Bottom)
   - **🗑️ Clear Memory**: Delete all thinking memory
     - Shows confirmation dialog
     - "Are you sure? This will delete all agent insights and observations."
     - Option to keep trade history, only clear thinking memory
   - **📥 Export**: Download thinking memory as .zip
   - **Close**: Close modal

**Modal Behavior**:
- Full-screen overlay (darkens background)
- Centered, responsive width (max 800px)
- ESC key to close
- Click outside to close
- Smooth fade-in animation

**Scrolling**:
- Thinking memory section has fixed height (400px)
- Independent scrollbar
- Smooth scroll behavior
- "Back to top" button appears when scrolled down

**Clear Memory Function**:
```tsx
function clearAgentMemory() {
  if (confirm("Are you sure you want to clear agent memory?")) {
    // Delete all thinking memory files
    await api.delete('/memory/thinking');
    
    // Show success message
    toast.success("Agent memory cleared successfully");
    
    // Close modal
    closeModal();
  }
}
```

**Files**:
- `src/ui/components/AgentInsightsModal.tsx` (NEW)
- `src/ui/components/MemoryViewer.tsx` (NEW)
- `src/ui/styles/modal.css` (NEW)
- `src/api/memory.ts` (NEW - API endpoints)

---

## Implementation Priority

**Week 1**:
- [ ] Sticky header
- [ ] News ticker (CoinMarketCap API)
- [ ] Theme system setup (⬤ light / ⏾ dark)

**Week 2**:
- [ ] 3-column layout
- [ ] Left column components
- [ ] Center column components

**Week 3**:
- [ ] Right column components
- [ ] Agent Insights button (opens modal)
- [ ] Dark/light mode toggle
- [ ] Branding implementation

**Week 4**:
- [ ] Fixed footer
- [ ] Agent Insights Modal (scrollable, clear function) ⭐
- [ ] Animations and polish
- [ ] Responsive testing
- [ ] Accessibility review

---

## Responsive Design

### Desktop (>1920px)
- Full 3-column layout
- All components visible
- Optimal information density

### Laptop (1280-1920px)
- Maintain 3 columns
- Slightly reduce padding
- Font sizes adjust

### Tablet (768-1280px)
- 2 columns: Left+Center merged, Right separate
- Some components stack

### Mobile (<768px)
- Single column, stacked
- Collapsible sections
- Bottom navigation

---

## Accessibility

### Requirements
- WCAG AA color contrast
- Keyboard navigation support
- Screen reader friendly
- Focus indicators
- Semantic HTML
- ARIA labels

### Testing
- [ ] Keyboard only navigation works
- [ ] Screen reader announces changes
- [ ] Color contrast ratios pass
- [ ] Focus states visible
- [ ] Alt text on all images

---

## Performance

### Optimization
- Lazy load components
- Virtual scrolling for long lists
- Debounce real-time updates
- Optimize re-renders
- Code splitting

### Targets
- Initial load: < 3 seconds
- Real-time update lag: < 500ms
- Smooth 60fps animations
- Lighthouse score: > 90

---

## Testing Checklist

- [ ] Header stays sticky on scroll
- [ ] News ticker scrolls smoothly
- [ ] Theme toggle works (⬤ light / ⏾ dark)
- [ ] All columns render correctly
- [ ] Portfolio equity updates real-time
- [ ] Order book shows live data
- [ ] Manual close buttons work
- [ ] Agent console scrolls properly
- [ ] Recent trades update correctly
- [ ] Agent Insights button opens modal ⭐
- [ ] Modal displays performance summary ⭐
- [ ] Modal shows thinking memory with scroll ⭐
- [ ] Modal scrollbar works smoothly ⭐
- [ ] Clear Memory button shows confirmation ⭐
- [ ] Clear Memory deletes thinking files ⭐
- [ ] Export button downloads memory ⭐
- [ ] Modal closes on ESC key ⭐
- [ ] Modal closes on outside click ⭐
- [ ] Account info accurate
- [ ] Footer always visible
- [ ] P&L updates in real-time
- [ ] Responsive on all screen sizes
- [ ] Dark/light mode consistent
- [ ] Animations smooth

---

## Design Assets Needed

### Icons
- Light mode icon: ⬤
- Dark mode icon: ⏾
- Close icon (✕)
- Copy icon (📋)
- Settings icon (⚙️)
- Refresh icon (🔄)
- Brain icon (🧠)

### Logo
- Spiral galaxy (blue/purple)
- Multiple sizes
- SVG format (scalable)
- Works in dark + light mode

### Colors
- Gradient for accents
- Color palette for both themes
- Status colors (green/yellow/red)

---

## Notes

### OpenRouter Style Reference
- Clean, modern aesthetic
- High contrast in dark mode
- Subtle animations
- Professional typography
- Minimal visual noise

### Hyperliquid Account Panel Reference
- Compact information display
- Clear hierarchy
- Wallet address formatting: `0xA871...8078`
- Copy button with feedback

### User Feedback
- Show preparation phase progress
- Display agent "thinking" status
- Confirm actions (close position, etc.)
- Success/error messages