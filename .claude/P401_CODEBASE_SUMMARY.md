# IDX Stock Screener - Codebase Structure & Architecture

## Project Overview

The IDX Stock Screener is a pattern-based stock screening system built with:
- **Backend**: Python (Flask)
- **Frontend**: Vanilla JavaScript + HTML/CSS
- **Database**: SQLite
- **Architecture**: Flask REST API with client-side pattern selection and results display

---

## 1. PATTERN SYSTEM ARCHITECTURE

### Pattern Definition Structure
Patterns are stored in the database with both technical and fundamental criteria.

**Database Schema:**
```sql
CREATE TABLE screening_patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    technical_criteria TEXT,  -- JSON string
    fundamental_criteria TEXT, -- JSON string
    sort_by TEXT,
    created_by TEXT DEFAULT 'system',
    is_preset BOOLEAN DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Pattern Categories
- **value**: Low valuation metrics (P/E, P/B)
- **growth**: Revenue/EPS growth metrics
- **quality**: Financial strength and profitability
- **health**: Liquidity and debt metrics
- **technical**: Technical signal-based patterns
- **composite**: Combined fundamental + technical patterns

### 10 Preset Patterns Available

1. **Cheap Quality on Reversal** (value)
   - Signals: golden_cross, rsi_oversold, bullish_macd
   - Fundamental: P/E ≤ 15, ROE ≥ 15%, Debt/Assets ≤ 0.4

2. **High Growth Momentum** (growth)
   - Signals: bullish_trend, rsi_bullish, macd_positive
   - Fundamental: Revenue Growth ≥ 20%, EPS Growth ≥ 15%, ROE ≥ 12%

3. **GARP** (growth)
   - Pure fundamental: PEG ≤ 1.0, EPS Growth ≥ 10%, ROE ≥ 12%, P/E ≤ 25

4. **Magic Formula** (quality)
   - Pure fundamental: ROIC ≥ 12%, EV/EBITDA ≤ 15

5. **Oversold Bounce** (technical)
   - Signals: rsi_oversold, stochastic_oversold
   - Fundamental: ROE ≥ 10%

6. **Blue Chip Quality** (quality)
   - Pure fundamental: Piotroski ≥ 7, ROE ≥ 15%, Current Ratio ≥ 2.0, Debt/Assets ≤ 0.5, Market Cap ≥ 10B

7. **Deep Value** (value)
   - Pure fundamental: P/B ≤ 1.0, P/E ≤ 10, ROE ≥ 5%

8. **Financial Fortress** (health)
   - Pure fundamental: Piotroski ≥ 7, Current Ratio ≥ 2.0, Debt/Assets ≤ 0.3, Altman Z-Score ≥ 3.0

9. **Small Cap Growth** (growth)
   - Pure fundamental: Market Cap 500M-5B, Revenue Growth ≥ 25%, EPS Growth ≥ 20%

10. **Breakout with Volume** (technical)
    - Signals: bullish_breakout, volume_surge, rsi_bullish
    - Fundamental: Market Cap ≥ 1B

---

## 2. TECHNICAL SIGNALS AVAILABLE

### Signal Type Enum
```python
class SignalType(Enum):
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
```

### Signal Direction Enum
```python
class SignalDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
```

### TREND SIGNALS (TrendSignalDetector)
- **Golden Cross**: SMA50 crosses above SMA200 (BULLISH)
  - Base Strength: 60, Confirmed by volume/ADX > 25
  
- **Death Cross**: SMA50 crosses below SMA200 (BEARISH)
  - Base Strength: 60
  
- **Fast Cross**: SMA20 crosses SMA50 (BULLISH/BEARISH)
  - Faster moving average signal
  
- **MACD Crossover**: MACD line crosses signal line
  - Direction depends on cross direction
  
- **MACD Histogram Reversal**: Histogram changes sign (trend reversal)
  
- **MA Slope Change**: Moving average slope direction reversal

### MOMENTUM SIGNALS (MomentumSignalDetector)
- **RSI Oversold** (< 30): BULLISH, strength 45-55
  - Bouncing bonus: +10 strength if RSI rising
  
- **RSI Overbought** (> 70): BEARISH, strength 45-55
  - Rolling over bonus: +10 strength if RSI falling
  
- **RSI Bullish Midline Cross**: RSI crosses 50 upward (BULLISH)
  - Strength: 50
  
- **RSI Bearish Midline Cross**: RSI crosses 50 downward (BEARISH)
  - Strength: 50
  
- **Stochastic Crossover**: K crosses D line (BULLISH/BEARISH)
  - Direction depends on cross
  
- **Stochastic Oversold/Overbought**: K < 20 or K > 80
  - Strength: 50-60
  
- **CCI Extreme**: CCI > 100 or CCI < -100
  - Strength varies by magnitude
  
- **Williams %R Extreme**: Reaches extreme levels
  
- **RSI Divergence**: Price makes new high/low but RSI doesn't (reversal signal)
  - Strength: 55-65

### VOLATILITY SIGNALS (VolatilitySignalDetector)
- **Bollinger Band Squeeze**: Low volatility (potential breakout)
  - Base Strength: 60
  
- **Bollinger Band Bullish Breakout**: Price breaks upper band (BULLISH)
  - Base Strength: 60
  
- **Bollinger Band Bearish Breakout**: Price breaks lower band (BEARISH)
  - Base Strength: 60
  
- **Walking Upper Band**: Price stays near upper band (strong uptrend)
  - BULLISH, strength 70
  
- **Walking Lower Band**: Price stays near lower band (strong downtrend)
  - BEARISH, strength 70
  
- **ATR Expansion**: Average True Range expands (increased volatility)
  - Direction: NEUTRAL, strength 50

### VOLUME SIGNALS (VolumeSignalDetector)
- **Volume Breakout**: Volume spike above average
  - Base Strength: 65
  - Direction: Determined by price action
  - Confirmation: Volume > 2x average

### Signal Strength Calculation
```python
def calculate_strength(
    base_strength: float,
    volume_confirmed: bool = False,      # +20 points
    trend_aligned: bool = False,         # +15 points
    multiple_indicators: int = 0         # +10 points each (max 30)
) -> float:  # Returns 0-100
```

---

## 3. FUNDAMENTAL METRICS AVAILABLE

### Valuation Metrics
- **P/E Ratio**: Price-to-Earnings (market cap / net income)
  - Good: < 15
  - Excellent: < 10
  
- **P/B Ratio**: Price-to-Book (market cap / equity)
  - Below Book: < 1.0
  - Good: < 2.0
  
- **P/S Ratio**: Price-to-Sales (market cap / revenue)
  - Good: < 2.0
  
- **PEG Ratio**: P/E / Growth Rate
  - Good: < 1.0 (reasonable price for growth)

### Profitability Metrics
- **ROE %**: Return on Equity (net income / equity)
  - Good: > 15%
  - Excellent: > 20%
  
- **ROA %**: Return on Assets (net income / total assets)
  - Good: > 10%
  
- **ROIC**: Return on Invested Capital
  - Good: > 12%
  
- **Net Profit Margin %**: (Net Income / Revenue)
  - Good: > 10%

### Growth Metrics
- **Revenue Growth YoY**: Year-over-year revenue growth %
  - Good: > 20%
  
- **EPS Growth YoY**: Earnings-per-share growth %
  - Good: > 15%

### Financial Health Metrics
- **Debt-to-Assets**: Total Liabilities / Total Assets
  - Good: < 0.4
  - Acceptable: < 0.5
  - High Risk: > 0.7
  
- **Debt-to-Equity**: Total Liabilities / Equity
  - Good: < 1.0
  
- **Current Ratio**: Current Assets / Current Liabilities
  - Good: > 2.0
  - Acceptable: > 1.0
  
- **Quick Ratio**: (Current Assets - Inventory) / Current Liabilities
  - Good: > 1.0
  
- **Working Capital**: Current Assets - Current Liabilities
  - Positive: Good

### Quality Scores
- **Piotroski F-Score**: 9-point financial strength score
  - Range: 0-9
  - Good: ≥ 7
  - Excellent: = 9
  
- **Altman Z-Score**: Bankruptcy prediction score
  - Range: 0-10
  - Safe: > 3.0
  - Distress: < 1.8

### Other Metrics
- **Market Cap**: Total market capitalization
  
- **EV/EBITDA**: Enterprise Value / EBITDA
  - Good: < 15

---

## 4. SCREENING LOGIC & PATTERN EXECUTION

### PatternEngine Class (`src/patterns/engine.py`)

**Main Methods:**
1. `run_pattern(pattern_id, use_cache=True, limit=100)` - Run screening
2. `create_pattern(pattern_data)` - Create custom pattern
3. `update_pattern(pattern_id, updates)` - Update existing pattern
4. `delete_pattern(pattern_id)` - Delete custom pattern
5. `list_patterns(include_custom=True)` - Get all patterns

### Execution Flow

```
run_pattern()
  ├─ Check cache (if use_cache=True)
  ├─ If cached and fresh: return cached results
  └─ If not cached or stale:
      ├─ Load pattern definition
      ├─ _execute_pattern()
      │  ├─ _screen_fundamentals() [if fundamental_criteria exist]
      │  │  └─ Call appropriate fundamental screener method
      │  │     (screen_garp, screen_magic_formula, screen_low_pe, etc.)
      │  └─ _screen_technical() [if technical_criteria exist]
      │     └─ Query signals table for matching stocks
      │        (Filter by signal names, min strength, active status)
      ├─ _score_results()
      │  ├─ Calculate match_score (weighted combination)
      │  │  ├─ Pure technical: technical_score
      │  │  ├─ Pure fundamental: fundamental_score
      │  │  └─ Combined: 60% fundamental + 40% technical
      │  └─ Sort results (by match_score or custom field)
      └─ Save to pattern_results_cache
```

### Scoring System

**Fundamental Score** (0-100):
- Points distributed equally across criteria
- Each criterion either meets range or doesn't (binary)
- Score = (met criteria / total criteria) * 100

**Technical Score** (0-100):
- Average signal strength of matching signals
- Based on signal strength values

**Combined Score**:
- Pure technical pattern: technical_score
- Pure fundamental pattern: fundamental_score
- Combined pattern: (fundamental_score * 0.6) + (technical_score * 0.4)

### Fundamental Screening Methods
```python
# Value Screening
- screen_low_pe(max_pe=15.0)
- screen_low_pb(max_pb=1.5)
- screen_low_ps(max_ps=2.0)

# Growth Screening
- screen_revenue_growth(min_growth=20.0)
- screen_eps_growth(min_growth=15.0)

# Quality Screening
- screen_high_roe(min_roe=15.0)
- screen_high_piotroski(min_score=7)
- screen_high_roic(min_roic=12.0)

# Health Screening
- screen_strong_liquidity(min_current=2.0)
- screen_low_debt(max_debt=0.4)
- screen_financial_strength()

# Composite Screening
- screen_garp(max_peg=1.0, min_growth=10, min_roe=12)
- screen_magic_formula(min_roic=12, max_ev=15)
```

### Cache Management
- **Table**: `pattern_results_cache`
- **TTL**: 24 hours (configurable via `cache_max_age_hours`)
- **Stored Data**: match_score, matched_signals (JSON), matched_fundamentals (JSON)
- **Auto-cleanup**: Old signals deactivated based on `signals.signal_expiry_days` config

---

## 5. FRONTEND ARCHITECTURE

### HTML Structure (`web/index.html`)

**Main Sections:**
1. **Header**: Application title
2. **Pattern Selector** (`#pattern-selector`)
   - Dropdown for pattern selection
   - Run Screen button
   - Details button
   - Pattern Details Panel (collapsible)
3. **Stock Analyzer** (`#stock-analyzer`)
   - Input for stock code
   - Analyze button
4. **Results Section** (`#results-section`)
   - Loading indicator
   - Results table/analysis display

### Frontend Components (`web/app.js`)

**State Variables:**
```javascript
patterns = {
    presets: [],  // All preset patterns
    custom: [],   // User-created patterns
    counts: {}    // {preset: N, custom: M, total: X}
}
selectedPattern = null;  // Currently selected pattern object
currentResults = [];     // Latest screening results
```

**Core Functions:**

1. **Pattern Management**
   - `loadPatterns()` - Fetch patterns from API
   - `populatePatternDropdown()` - Populate select with grouped categories
   - `handlePatternChange(e)` - Load pattern details on selection change
   - `showPatternDetails()` - Display criteria in modal
   - `hidePatternDetails()` - Close modal

2. **Screening Execution**
   - `runScreening()` - Execute pattern (POST to API)
   - `displayResults(data)` - Render results table
   - `getScoreClass(score)` - Determine CSS class based on score

3. **Stock Analysis**
   - `analyzeStock()` - Fetch individual stock signals/fundamentals
   - `displayStockAnalysis(data)` - Render signal and fundamental breakdown

4. **Formatting Helpers**
   - `formatSignalName(name)` - Convert snake_case to Title Case
   - `formatMetricName(name)` - Use mapping dictionary for metric names
   - `formatSignals(signals)` - Render signal badges
   - `formatFundamentals(fundamentals)` - Render metric grid

### Frontend to Backend Communication

**GET /api/patterns**
```javascript
Response:
{
    presets: [
        {
            pattern_id: "cheap_quality_reversal",
            pattern_name: "Cheap Quality on Reversal",
            category: "value",
            description: "...",
            is_preset: true
        },
        ...
    ],
    custom: [...],
    counts: {preset: 10, custom: 0, total: 10}
}
```

**GET /api/patterns/{pattern_id}**
```javascript
Response:
{
    pattern_id: "cheap_quality_reversal",
    pattern_name: "Cheap Quality on Reversal",
    category: "value",
    description: "...",
    technical_criteria: {
        signals: ["golden_cross", "rsi_oversold", "bullish_macd"],
        min_signal_strength: 70
    },
    fundamental_criteria: {
        pe_ratio: {min: 0, max: 15},
        roe_percent: {min: 15, max: 999},
        debt_to_assets: {min: 0, max: 0.4}
    },
    sort_by: "signal_strength",
    is_preset: true
}
```

**POST /api/patterns/{pattern_id}/run**
```javascript
Request:
{
    limit: 50,
    use_cache: true
}

Response:
{
    pattern: {
        pattern_id: "...",
        pattern_name: "...",
        description: "...",
        category: "..."
    },
    results: [
        {
            stock_id: "BBCA",
            match_score: 85,
            signals: [
                {name: "Golden Cross", strength: 85},
                ...
            ],
            fundamentals: {
                pe_ratio: 12.5,
                roe_percent: 21.3,
                ...
            }
        },
        ...
    ],
    total_found: 45,
    execution_time: 1.23
}
```

### Results Display

**Table Columns:**
1. Stock - Stock symbol badge
2. Match Score - Color-coded badge (high/medium/low)
3. Signals - Top 3 signals with strength values
4. Fundamentals - Key metrics (P/E, P/B, ROE, Growth, PEG, ROIC, F-Score)

**Stock Analysis Display:**
- Technical Signals Card
  - Summary: Count of bullish/bearish/neutral/total signals
  - Detailed list with direction, strength/value, type, date
- Fundamental Metrics Card
  - Grid display of key metrics with labels and values

---

## 6. PROJECT STRUCTURE

```
/Users/raymonmudrig/AI/Screener/
├── web/                           # Frontend
│   ├── index.html                 # Main HTML page
│   ├── app.js                     # All frontend logic (vanilla JS)
│   └── style.css                  # Styling
│
├── src/                           # Backend Python modules
│   ├── patterns/                  # Pattern system
│   │   ├── engine.py              # PatternEngine (execution)
│   │   └── storage.py             # PatternStorage (CRUD)
│   │
│   ├── signals/                   # Technical signal detection
│   │   ├── engine.py              # SignalEngine (orchestrator)
│   │   ├── detector.py            # Base classes (Signal, SignalType, etc.)
│   │   ├── trend_signals.py       # TrendSignalDetector
│   │   ├── momentum_signals.py    # MomentumSignalDetector
│   │   ├── volatility_signals.py  # VolatilitySignalDetector
│   │   └── volume_signals.py      # VolumeSignalDetector
│   │
│   ├── fundamentals/              # Fundamental analysis
│   │   ├── screener.py            # FundamentalScreener (main logic)
│   │   ├── ratios.py              # RatioCalculator (static methods)
│   │   ├── growth.py              # GrowthCalculator
│   │   ├── quality.py             # QualityScorer
│   │   ├── ttm.py                 # TTMCalculator
│   │   ├── storage.py             # FundamentalDataStorage
│   │   └── fetcher.py             # FundamentalDataFetcher
│   │
│   ├── indicators/                # Technical indicators
│   │   ├── calculator.py          # IndicatorCalculator
│   │   ├── trend.py               # Trend indicators
│   │   ├── momentum.py            # Momentum indicators
│   │   ├── volatility.py          # Volatility indicators
│   │   └── volume.py              # Volume indicators
│   │
│   ├── api/                       # REST API
│   │   ├── web.py                 # Flask app & endpoints
│   │   └── cli.py                 # CLI interface
│   │
│   ├── data/                      # Data management
│   │   ├── fetcher.py             # Data fetcher
│   │   ├── storage.py             # Data storage
│   │   └── validator.py           # Data validation
│   │
│   └── utils/                     # Utilities
│       ├── db.py                  # DatabaseManager
│       ├── config.py              # Configuration
│       └── logger.py              # Logging
│
├── scripts/                       # Setup & maintenance scripts
│   ├── create_pattern_tables.py   # Initialize pattern tables & presets
│   ├── init_db.py                 # Initialize database
│   ├── batch_update.py            # Batch data updates
│   ├── scheduler_intraday.py      # Background scheduler
│   └── check_db.py                # Database verification
│
├── database/                      # SQLite database
│   └── stockCode.sqlite           # Main database file
│
├── config/                        # Configuration files
├── logs/                          # Log files
├── data/                          # Data files
└── requirements.txt               # Python dependencies
```

---

## 7. DATABASE SCHEMA SUMMARY

### Pattern System Tables
```sql
-- Screening Patterns
screening_patterns (
    pattern_id,
    pattern_name,
    description,
    category,
    technical_criteria (JSON),
    fundamental_criteria (JSON),
    sort_by,
    created_by,
    is_preset,
    created_at,
    updated_at
)

-- Pattern Results Cache
pattern_results_cache (
    pattern_id,
    stock_id,
    match_score,
    matched_signals (JSON),
    matched_fundamentals (JSON),
    last_updated
)
```

### Signal Tables
```sql
-- Technical signals detected
signals (
    stock_id,
    signal_type (trend/momentum/volatility/volume),
    signal_name,
    strength (0-100),
    detected_date,
    is_active,
    metadata (JSON)
)

-- Indicators calculated
indicators (
    stock_id,
    indicator_name,
    value,
    date
)
```

### Fundamental Data Tables
```sql
-- Fundamental metrics by quarter
fundamental_data (
    stock_id,
    year,
    quarter,
    pe_ratio,
    pb_ratio,
    roe_percent,
    revenue_growth_yoy,
    eps_growth_yoy,
    peg_ratio,
    roic,
    piotroski_score,
    altman_z_score,
    current_ratio,
    debt_to_assets,
    debt_to_equity,
    close_price,
    ... (many more)
)
```

---

## 8. KEY CONFIGURATION AREAS

### Signal Configuration
- RSI thresholds: oversold (30), overbought (70)
- Volume confirmation: > 1.5x average volume
- Trend alignment: SMA50 vs SMA200 comparison
- Signal expiry: 5 days default

### Pattern Scoring
- Combined weighting: 60% fundamental, 40% technical
- Cache TTL: 24 hours default
- Results limit: Configurable (default 100)

### Database
- Path: `database/stockCode.sqlite`
- Type: SQLite3
- Indexes on: pattern categories, preset flag, cache metrics

---

## 9. API ENDPOINTS

### Pattern Management
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/patterns` | List all patterns with counts |
| GET | `/api/patterns/<id>` | Get pattern details |
| POST | `/api/patterns/<id>/run` | Execute pattern screening |
| POST | `/api/patterns` | Create custom pattern |
| PUT | `/api/patterns/<id>` | Update pattern |
| DELETE | `/api/patterns/<id>` | Delete custom pattern |

### Stock Analysis
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/stocks/<id>/analysis` | Get stock signals & fundamentals |

### Frontend
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Serve index.html |
| GET | `/*` | Serve static files (CSS, JS) |

---

## 10. IMPLEMENTATION NOTES FOR CUSTOM PATTERNS

### Creating Custom Patterns

**Structure:**
```json
{
    "pattern_id": "my_custom_pattern",
    "pattern_name": "My Strategy Name",
    "category": "custom",
    "description": "Pattern description",
    "technical_criteria": {
        "signals": ["golden_cross", "rsi_oversold"],
        "min_signal_strength": 70
    },
    "fundamental_criteria": {
        "pe_ratio": {"min": 0, "max": 15},
        "roe_percent": {"min": 15, "max": 999}
    },
    "sort_by": "match_score"
}
```

**Available Signal Names:**
- Trend: golden_cross, death_cross, fast_cross, bullish_breakout, bullish_trend
- Momentum: rsi_oversold, rsi_overbought, rsi_bullish, macd_positive, stochastic_oversold, stochastic_overbought
- Volatility: bollinger_squeeze, bollinger_breakout
- Volume: volume_surge

**Available Metric Fields:**
All metrics in Fundamental Metrics section above can be used with {min, max} ranges.

**Sorting Options:**
- match_score (default)
- Any fundamental metric field (pe_ratio, revenue_growth_yoy, etc.)

---

## Summary

This is a full-stack stock screening application that:
1. Stores predefined and custom screening patterns
2. Executes patterns against a stock database
3. Uses technical signals (trend, momentum, volatility, volume) detected from price data
4. Evaluates fundamental metrics (valuation, profitability, growth, health)
5. Scores and ranks results using weighted combination
6. Caches results for performance
7. Provides a user-friendly web interface for pattern selection and result exploration

The system is extensible - new patterns can be created by combining different signals and metrics through the API or UI.
