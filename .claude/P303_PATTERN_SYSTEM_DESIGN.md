# Pattern-Based Screener System Design

**Purpose:** Simple, user-friendly screening through predefined and custom patterns
**Target:** Web GUI with pattern selection, editing, and creation

---

## 🎯 Core Concept: Patterns

**A Pattern** = Named combination of technical and/or fundamental criteria

### Pattern Structure
```json
{
  "pattern_id": "cheap_quality_reversal",
  "pattern_name": "Cheap Quality Stock on Reversal",
  "description": "Undervalued quality companies showing technical reversal",
  "category": "value",
  "technical_criteria": {
    "signals": ["golden_cross", "rsi_oversold"],
    "min_signal_strength": 70
  },
  "fundamental_criteria": {
    "pe_ratio": {"min": 0, "max": 15},
    "roe_percent": {"min": 15, "max": 999},
    "debt_to_assets": {"min": 0, "max": 0.4},
    "market_cap": {"min": 1000000000, "max": null}
  },
  "sort_by": "signal_strength",
  "created_by": "system",
  "is_preset": true
}
```

---

## 📦 Pattern Categories

### 1. **Value Patterns**
- Cheap Quality Companies
- Deep Value Stocks
- Below Book Value
- Margin of Safety

### 2. **Growth Patterns**
- High Growth Momentum
- GARP (Growth at Reasonable Price)
- Accelerating Growth
- Small Cap Growth

### 3. **Quality Patterns**
- Blue Chip Quality
- Magic Formula
- High ROE Companies
- Financial Fortress

### 4. **Technical Patterns**
- Bullish Breakout
- Oversold Bounce
- Trend Following
- Momentum Surge

### 5. **Combined Patterns**
- Value + Reversal
- Growth + Momentum
- Quality + Undervalued
- Defensive + Yield

---

## 🎨 GUI Design (Simple)

### Main Screen

```
┌─────────────────────────────────────────────────────────────┐
│  IDX Stock Screener                    [Refresh] [Settings] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Select Pattern:  [Cheap Quality on Reversal ▼]             │
│                   [  Edit  ] [  New  ] [ Delete ] [ Save ]  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Results: 23 stocks found                    [Export CSV]   │
│                                                             │
│  Stock  | Price | Signals              | P/E | ROE% | Score │
│  ───────────────────────────────────────────────────────────│
│  BBCA   | 8,750 | Golden Cross, RSI:65 | 12  | 21.3 | 85/100│
│  BMRI   | 6,450 | Bullish MACD, RSI:58 | 9.5 | 18.7 | 82/100│
│  TLKM   | 3,520 | Golden Cross         | 14  | 22.1 | 78/100│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Edit Pattern Screen

```
┌────────────────────────────────────────────────────────────┐
│  Edit Pattern: Cheap Quality on Reversal                   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─── Technical Criteria ────────────────────────────────┐ │
│  │                                                       │ │
│  │  Select Signals:                                      │ │
│  │  [x] Golden Cross         [x] Bullish MACD            │ │
│  │  [ ] Death Cross          [x] RSI Oversold            │ │
│  │  [ ] Bearish MACD         [ ] RSI Overbought          │ │
│  │  [x] Bullish Volume       [ ] Stochastic Oversold     │ │
│  │                                                       │ │
│  │  Minimum Signal Strength: [====|====] 70              │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌─── Fundamental Criteria ──────────────────────────────┐ │
│  │                                                       │ │
│  │  P/E Ratio:     [0    ] ≤ P/E ≤ [15   ]               │ │
│  │  P/B Ratio:     [0    ] ≤ P/B ≤ [3    ]               │ │
│  │  ROE %:         [15   ] ≤ ROE ≤ [999  ]               │ │
│  │  Debt/Assets:   [0    ] ≤ D/A ≤ [0.4  ]               │ │
│  │  Market Cap:    [1B   ] ≤ Cap ≤ [No Limit]            │ │
│  │  Revenue Growth:[10   ] ≤ Growth (%) ≤ [999  ]        │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                            │
│             [  Cancel  ]  [  Save Pattern  ]               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🔧 System Architecture

### Pattern Storage (SQLite)

```sql
CREATE TABLE screening_patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    technical_criteria TEXT,  -- JSON
    fundamental_criteria TEXT, -- JSON
    sort_by TEXT,
    created_by TEXT,
    is_preset BOOLEAN DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE pattern_results_cache (
    pattern_id TEXT,
    stock_id TEXT,
    match_score INTEGER,
    matched_signals TEXT, -- JSON
    matched_fundamentals TEXT, -- JSON
    last_updated TIMESTAMP,
    PRIMARY KEY (pattern_id, stock_id)
);
```

### Pattern Engine (Python)

```python
class PatternEngine:
    def __init__(self):
        self.db = DatabaseManager()
        self.technical_screener = SignalEngine()
        self.fundamental_screener = FundamentalScreener()

    def run_pattern(self, pattern_id):
        """Run a screening pattern and return matching stocks"""
        pattern = self.load_pattern(pattern_id)

        # Get stocks matching fundamental criteria
        fundamental_matches = self.screen_fundamentals(
            pattern['fundamental_criteria']
        )

        # Get stocks matching technical criteria
        technical_matches = self.screen_technical(
            pattern['technical_criteria']
        )

        # Combine and score
        results = self.combine_and_score(
            fundamental_matches,
            technical_matches,
            pattern
        )

        return results

    def create_pattern(self, pattern_data):
        """Create a new custom pattern"""
        pass

    def update_pattern(self, pattern_id, updates):
        """Update pattern criteria"""
        pass

    def delete_pattern(self, pattern_id):
        """Delete a custom pattern"""
        pass
```

---

## 📋 Preset Patterns

### 1. Cheap Quality on Reversal ⭐
**Category:** Value + Technical
```json
{
  "pattern_name": "Cheap Quality on Reversal",
  "technical_criteria": {
    "signals": ["golden_cross", "rsi_oversold", "bullish_macd"],
    "min_signal_strength": 70
  },
  "fundamental_criteria": {
    "pe_ratio": {"max": 15},
    "roe_percent": {"min": 15},
    "debt_to_assets": {"max": 0.4}
  }
}
```

### 2. High Growth Momentum 🚀
**Category:** Growth + Technical
```json
{
  "pattern_name": "High Growth Momentum",
  "technical_criteria": {
    "signals": ["bullish_trend", "rsi_bullish", "macd_positive"],
    "min_signal_strength": 75
  },
  "fundamental_criteria": {
    "revenue_growth_yoy": {"min": 20},
    "eps_growth_yoy": {"min": 15},
    "roe_percent": {"min": 12}
  }
}
```

### 3. GARP (Growth at Reasonable Price) 💎
**Category:** Growth + Value
```json
{
  "pattern_name": "GARP - Growth at Reasonable Price",
  "fundamental_criteria": {
    "peg_ratio": {"max": 1.0},
    "eps_growth_yoy": {"min": 10},
    "roe_percent": {"min": 12},
    "pe_ratio": {"max": 25}
  }
}
```

### 4. Magic Formula (Quality + Value) ⚡
**Category:** Quality + Value
```json
{
  "pattern_name": "Magic Formula",
  "fundamental_criteria": {
    "roic": {"min": 12},
    "ev_ebitda": {"max": 15}
  },
  "sort_by": "roic_rank"
}
```

### 5. Oversold Bounce 📈
**Category:** Technical
```json
{
  "pattern_name": "Oversold Bounce",
  "technical_criteria": {
    "signals": ["rsi_oversold", "stochastic_oversold"],
    "min_signal_strength": 70
  },
  "fundamental_criteria": {
    "roe_percent": {"min": 10}  // Ensure quality
  }
}
```

### 6. Blue Chip Quality 🏆
**Category:** Quality
```json
{
  "pattern_name": "Blue Chip Quality",
  "fundamental_criteria": {
    "piotroski_score": {"min": 7},
    "roe_percent": {"min": 15},
    "current_ratio": {"min": 2.0},
    "debt_to_assets": {"max": 0.5},
    "market_cap": {"min": 10000000000}  // 10B minimum
  }
}
```

### 7. Deep Value 💰
**Category:** Value
```json
{
  "pattern_name": "Deep Value",
  "fundamental_criteria": {
    "pb_ratio": {"max": 1.0},  // Below book value
    "pe_ratio": {"max": 10},
    "roe_percent": {"min": 5}  // Some profitability
  }
}
```

### 8. Financial Fortress 🏰
**Category:** Health
```json
{
  "pattern_name": "Financial Fortress",
  "fundamental_criteria": {
    "piotroski_score": {"min": 7},
    "current_ratio": {"min": 2.0},
    "debt_to_assets": {"max": 0.3},
    "altman_z_score": {"min": 3.0},
    "cf_operating": {"min": 0}
  }
}
```

### 9. Small Cap Growth 🌱
**Category:** Growth
```json
{
  "pattern_name": "Small Cap Growth",
  "fundamental_criteria": {
    "market_cap": {"min": 500000000, "max": 5000000000},
    "revenue_growth_yoy": {"min": 25},
    "eps_growth_yoy": {"min": 20},
    "roe_percent": {"min": 15}
  }
}
```

### 10. Breakout with Volume 📊
**Category:** Technical
```json
{
  "pattern_name": "Breakout with Volume",
  "technical_criteria": {
    "signals": ["bullish_breakout", "volume_surge", "rsi_bullish"],
    "min_signal_strength": 75
  },
  "fundamental_criteria": {
    "market_cap": {"min": 1000000000}
  }
}
```

---

## 🔌 API Endpoints (For Web GUI)

### GET /api/patterns
```json
// List all available patterns
{
  "presets": [
    {
      "pattern_id": "cheap_quality_reversal",
      "pattern_name": "Cheap Quality on Reversal",
      "category": "value",
      "is_preset": true
    }
  ],
  "custom": [
    {
      "pattern_id": "my_custom_pattern",
      "pattern_name": "My Custom Strategy",
      "category": "custom",
      "is_preset": false
    }
  ]
}
```

### GET /api/patterns/:pattern_id
```json
// Get pattern details
{
  "pattern_id": "cheap_quality_reversal",
  "pattern_name": "Cheap Quality on Reversal",
  "description": "...",
  "technical_criteria": {...},
  "fundamental_criteria": {...}
}
```

### POST /api/patterns/:pattern_id/run
```json
// Run pattern screening
{
  "results": [
    {
      "stock_id": "BBCA",
      "stock_name": "Bank Central Asia",
      "price": 8750,
      "matched_signals": ["Golden Cross", "RSI Oversold"],
      "signal_strength": 85,
      "pe_ratio": 12.5,
      "roe_percent": 21.3,
      "market_cap": 930572533688,
      "match_score": 85
    }
  ],
  "total_found": 23
}
```

### POST /api/patterns
```json
// Create new pattern
{
  "pattern_name": "My Strategy",
  "technical_criteria": {...},
  "fundamental_criteria": {...}
}
```

### PUT /api/patterns/:pattern_id
```json
// Update pattern
{
  "fundamental_criteria": {
    "pe_ratio": {"max": 20}  // Updated value
  }
}
```

### DELETE /api/patterns/:pattern_id
```json
// Delete custom pattern
{
  "success": true
}
```

---

## 🎯 Implementation Steps

### Step 1: Pattern Database
```bash
# Create pattern tables
python3 scripts/create_pattern_tables.py
```

### Step 2: Pattern Engine
```bash
# Implement pattern engine
src/patterns/engine.py
src/patterns/storage.py
src/patterns/presets.py
```

### Step 3: CLI Integration
```bash
# Add pattern commands
python3 -m src.api.cli list-patterns
python3 -m src.api.cli run-pattern "cheap_quality_reversal"
python3 -m src.api.cli create-pattern --name "My Strategy" --config pattern.json
```

### Step 4: Web API
```bash
# Create Flask/FastAPI endpoints
src/api/web.py
```

### Step 5: Web GUI
```bash
# Simple HTML/JavaScript interface
web/index.html
web/app.js
```

---

## 📱 User Flow

### Flow 1: Use Preset Pattern
1. User opens web interface
2. Selects "Cheap Quality on Reversal" from dropdown
3. Clicks "Run Screen"
4. Views 23 matching stocks in table
5. Clicks stock to see details
6. Exports to CSV

### Flow 2: Customize Pattern
1. User selects "GARP" pattern
2. Clicks "Edit"
3. Changes P/E max from 25 to 20
4. Changes ROE min from 12 to 15
5. Clicks "Save As New Pattern"
6. Names it "Strict GARP"
7. Runs the new pattern

### Flow 3: Create New Pattern
1. User clicks "New Pattern"
2. Names it "My Dividend Strategy"
3. In Fundamental section:
   - Sets Dividend Yield: min 4%
   - Sets P/E: max 15
   - Sets Debt/Assets: max 0.5
4. In Technical section:
   - Checks "Bullish Trend"
   - Checks "RSI Bullish"
5. Clicks "Save"
6. Runs the pattern

---

## 🎨 GUI Component Design

### Pattern Selector Component
```javascript
<PatternSelector
  patterns={patterns}
  selectedPattern={currentPattern}
  onSelect={handlePatternSelect}
  onEdit={handlePatternEdit}
  onNew={handlePatternNew}
  onDelete={handlePatternDelete}
/>
```

### Results Table Component
```javascript
<ResultsTable
  results={screeningResults}
  columns={['Stock', 'Price', 'Signals', 'P/E', 'ROE%', 'Score']}
  onRowClick={handleStockClick}
  onExport={handleExport}
/>
```

### Pattern Editor Component
```javascript
<PatternEditor
  pattern={editingPattern}
  availableSignals={technicalSignals}
  availableMetrics={fundamentalMetrics}
  onChange={handlePatternChange}
  onSave={handlePatternSave}
  onCancel={handlePatternCancel}
/>
```

---

## 💡 Benefits of Pattern System

### For Users
✅ **Simple** - Click, select, run
✅ **No complexity** - Preset patterns for common strategies
✅ **Customizable** - Adjust parameters easily
✅ **Reusable** - Save and reuse patterns
✅ **Educational** - Learn from preset patterns

### For Developers
✅ **Modular** - Separate pattern logic from screening
✅ **Extensible** - Easy to add new patterns
✅ **Testable** - Test patterns independently
✅ **Cacheable** - Cache pattern results
✅ **API-friendly** - Clean REST endpoints

---

## 📊 Sample Use Cases

### Use Case 1: Beginner Investor
- Opens screener
- Sees preset patterns: "Blue Chip Quality", "GARP", "Magic Formula"
- Selects "Blue Chip Quality"
- Clicks "Run"
- Gets 15 high-quality, low-risk stocks
- Researches top 3
- Makes investment decision

### Use Case 2: Experienced Trader
- Creates custom pattern: "My Swing Strategy"
- Technical: Golden Cross + RSI 50-70
- Fundamental: P/E < 15, ROE > 12%
- Saves pattern
- Runs daily at market open
- Gets 5-10 setups
- Enters trades

### Use Case 3: Value Investor
- Uses "Deep Value" preset
- Edits to tighten criteria:
  - P/B < 0.8 (from 1.0)
  - P/E < 8 (from 10)
- Saves as "Ultra Deep Value"
- Runs weekly
- Finds 2-3 opportunities per month

---

**Next Steps:**
1. Implement pattern database schema
2. Create pattern engine
3. Add preset patterns
4. Build API endpoints
5. Create simple web interface

**Status:** Design Complete - Ready for Implementation
