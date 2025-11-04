# Custom Pattern Implementation Guide

## Quick Start: Adding Custom User Patterns

This guide explains how to implement custom user pattern features in the IDX Stock Screener.

---

## 1. PATTERN DEFINITION REFERENCE

### Pattern Structure
```json
{
    "pattern_id": "my_strategy_id",          // Unique identifier (alphanumeric + underscore)
    "pattern_name": "My Strategy Name",       // Display name (user-friendly)
    "category": "custom",                     // Pattern category
    "description": "Strategy description",    // User-provided explanation
    "technical_criteria": {
        "signals": ["signal1", "signal2"],    // Array of signal names to match
        "min_signal_strength": 70             // Minimum signal strength (0-100)
    },
    "fundamental_criteria": {
        "metric_name": {
            "min": 0,                         // Minimum value (optional)
            "max": 15                         // Maximum value (optional, 999 = no limit)
        },
        // ... more metrics
    },
    "sort_by": "match_score"                  // Sort field (default: "match_score")
}
```

---

## 2. AVAILABLE TECHNICAL SIGNALS

### Signal Names by Type

**Trend Signals:**
- `golden_cross` - SMA50 crosses above SMA200
- `death_cross` - SMA50 crosses below SMA200
- `fast_cross` - SMA20/SMA50 crossover
- `bullish_trend` - General bullish trend detected
- `bearish_trend` - General bearish trend detected
- `bullish_breakout` - Price breaks resistance with strength

**Momentum Signals:**
- `rsi_oversold` - RSI below 30 (potential bounce)
- `rsi_overbought` - RSI above 70 (potential reversal)
- `rsi_bullish` - RSI moving upward
- `rsi_bearish` - RSI moving downward
- `macd_positive` - MACD above signal line
- `macd_negative` - MACD below signal line
- `stochastic_oversold` - Stochastic K below 20
- `stochastic_overbought` - Stochastic K above 80
- `cci_extreme` - CCI in extreme territory
- `williams_extreme` - Williams %R at extreme

**Volatility Signals:**
- `bollinger_squeeze` - Low volatility setup
- `bollinger_breakout` - Price breaks Bollinger Band

**Volume Signals:**
- `volume_surge` - Volume spike above average

---

## 3. AVAILABLE FUNDAMENTAL METRICS

### Valuation Metrics
```python
"pe_ratio": {"min": 0, "max": 15}           # Price-to-Earnings
"pb_ratio": {"min": 0, "max": 1.5}          # Price-to-Book
"ps_ratio": {"min": 0, "max": 2.0}          # Price-to-Sales
"peg_ratio": {"min": 0, "max": 1.0}         # PEG Ratio
"ev_ebitda": {"min": 0, "max": 15}          # EV/EBITDA
```

### Profitability Metrics
```python
"roe_percent": {"min": 15, "max": 999}      # Return on Equity %
"roa_percent": {"min": 10, "max": 999}      # Return on Assets %
"roic": {"min": 12, "max": 999}             # Return on Invested Capital %
"npm_percent": {"min": 10, "max": 999}      # Net Profit Margin %
```

### Growth Metrics
```python
"revenue_growth_yoy": {"min": 20, "max": 999}  # Revenue Growth %
"eps_growth_yoy": {"min": 15, "max": 999}      # EPS Growth %
```

### Financial Health Metrics
```python
"current_ratio": {"min": 2.0, "max": 999}     # Current Ratio (liquidity)
"quick_ratio": {"min": 1.0, "max": 999}       # Quick Ratio
"debt_to_assets": {"min": 0, "max": 0.4}      # Debt-to-Assets ratio
"debt_to_equity": {"min": 0, "max": 1.0}      # Debt-to-Equity ratio
"cash_ratio": {"min": 0.5, "max": 999}        # Cash Ratio
```

### Quality Scores
```python
"piotroski_score": {"min": 7, "max": 9}    # Piotroski F-Score (0-9)
"altman_z_score": {"min": 3.0, "max": 999} # Altman Z-Score
```

### Other Metrics
```python
"market_cap": {"min": 1000000000, "max": None}  # Market Cap (in local currency)
```

---

## 4. PATTERN CATEGORIES

Choose one that best describes the pattern:

- **value** - Low valuation patterns (P/E, P/B focused)
- **growth** - High growth patterns (Revenue/EPS growth)
- **quality** - Quality/profitability focused patterns
- **health** - Financial strength and safety patterns
- **technical** - Technical signal based patterns
- **custom** - User-defined composite patterns

---

## 5. PATTERN EXAMPLES

### Example 1: Simple Value + Technical Pattern
```json
{
    "pattern_id": "value_breakout",
    "pattern_name": "Value with Breakout",
    "category": "value",
    "description": "Undervalued stocks breaking out with volume",
    "technical_criteria": {
        "signals": ["bullish_breakout", "volume_surge"],
        "min_signal_strength": 70
    },
    "fundamental_criteria": {
        "pe_ratio": {"min": 0, "max": 12},
        "pb_ratio": {"min": 0, "max": 1.2},
        "roe_percent": {"min": 10, "max": 999}
    },
    "sort_by": "match_score"
}
```

### Example 2: Growth Only (Fundamental Only)
```json
{
    "pattern_id": "aggressive_growth",
    "pattern_name": "Aggressive Growth",
    "category": "growth",
    "description": "High growth companies with strong fundamentals",
    "technical_criteria": {},
    "fundamental_criteria": {
        "revenue_growth_yoy": {"min": 30, "max": 999},
        "eps_growth_yoy": {"min": 25, "max": 999},
        "roe_percent": {"min": 15, "max": 999},
        "peg_ratio": {"min": 0, "max": 1.5}
    },
    "sort_by": "revenue_growth_yoy"
}
```

### Example 3: Technical Only (Signal Only)
```json
{
    "pattern_id": "momentum_confirmation",
    "pattern_name": "Momentum Confirmation",
    "category": "technical",
    "description": "Strong momentum signals with multiple confirmations",
    "technical_criteria": {
        "signals": ["rsi_bullish", "macd_positive", "volume_surge"],
        "min_signal_strength": 65
    },
    "fundamental_criteria": {},
    "sort_by": "match_score"
}
```

### Example 4: Quality + Conservative
```json
{
    "pattern_id": "safe_growth",
    "pattern_name": "Safe Growth",
    "category": "quality",
    "description": "Growing with financial safety",
    "technical_criteria": {},
    "fundamental_criteria": {
        "revenue_growth_yoy": {"min": 15, "max": 999},
        "piotroski_score": {"min": 7, "max": 9},
        "current_ratio": {"min": 1.5, "max": 999},
        "debt_to_assets": {"min": 0, "max": 0.5},
        "roe_percent": {"min": 12, "max": 999}
    },
    "sort_by": "piotroski_score"
}
```

---

## 6. IMPLEMENTATION OPTIONS

### Option A: Database Insert (via Python Script)
```python
from src.patterns.storage import PatternStorage

storage = PatternStorage('database/stockCode.sqlite')
pattern = {
    "pattern_id": "my_custom_pattern",
    "pattern_name": "My Custom Pattern",
    "category": "custom",
    "description": "My pattern description",
    "technical_criteria": {
        "signals": ["golden_cross"],
        "min_signal_strength": 70
    },
    "fundamental_criteria": {
        "pe_ratio": {"min": 0, "max": 15}
    }
}
storage.create_pattern(pattern)
```

### Option B: API POST (via HTTP Request)
```bash
curl -X POST http://localhost:5000/api/patterns \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "my_custom_pattern",
    "pattern_name": "My Custom Pattern",
    "category": "custom",
    "description": "My pattern description",
    "technical_criteria": {
      "signals": ["golden_cross"],
      "min_signal_strength": 70
    },
    "fundamental_criteria": {
      "pe_ratio": {"min": 0, "max": 15}
    }
  }'
```

### Option C: CLI Command (if implemented)
```bash
python3 -m src.api.cli create-pattern --file pattern.json
```

---

## 7. PATTERN VALIDATION RULES

**Required Fields:**
- `pattern_id` - Unique identifier (must not already exist)
- `pattern_name` - Display name
- `category` - One of: value, growth, quality, health, technical, custom

**Optional Fields:**
- `description` - Pattern explanation (recommended)
- `technical_criteria` - Empty object {} if no technical criteria
- `fundamental_criteria` - Empty object {} if no fundamental criteria
- `sort_by` - Default is "match_score"

**Constraints:**
- At least one criteria type must be non-empty (technical or fundamental)
- Signal names must match available signal names
- Metric names must match available fundamental metrics
- Min/max values should be reasonable (min <= max when both specified)
- Signal strength should be 0-100
- Pattern ID should be lowercase with underscores

---

## 8. PATTERN EXECUTION & SCORING

### How Patterns Work

1. **Load Pattern**: Retrieve pattern definition from database
2. **Screen Fundamentals**: Query stocks meeting fundamental criteria
3. **Screen Technical**: Query stocks with required signals
4. **Combine Results**: Merge fundamental and technical matches
5. **Score Results**:
   - Fundamental Score: % of met criteria
   - Technical Score: Average signal strength
   - Combined: 60% fundamental + 40% technical
6. **Sort & Cache**: Sort by specified field, cache for 24 hours

### Score Interpretation
- 80-100: Excellent match (high confidence)
- 60-79: Good match (moderate confidence)
- 40-59: Fair match (lower confidence)
- 0-39: Poor match (weak signal)

---

## 9. TESTING YOUR PATTERN

### Step 1: Create Pattern
Create pattern via API or database insert

### Step 2: Verify Pattern
```python
from src.patterns.storage import PatternStorage

storage = PatternStorage()
pattern = storage.get_pattern("my_custom_pattern")
print(pattern)  # Should return your pattern definition
```

### Step 3: Run Pattern
```python
from src.patterns.engine import PatternEngine

engine = PatternEngine()
results = engine.run_pattern("my_custom_pattern", limit=20)
for result in results:
    print(f"{result['stock_id']}: {result['match_score']}/100")
```

### Step 4: Check Frontend
- Open http://localhost:5000
- Select your pattern from dropdown
- Click "Run Screen" to execute
- View results table and click "Details" to see criteria

---

## 10. COMMON PATTERNS TO CREATE

### Value Investor Pattern
Combines low P/E with profitability and financial health
```python
{
    "pe_ratio": {"min": 0, "max": 12},
    "pb_ratio": {"min": 0, "max": 1.0},
    "roe_percent": {"min": 10, "max": 999},
    "debt_to_assets": {"min": 0, "max": 0.4}
}
```

### Growth at Reasonable Price (GARP)
High growth but reasonable valuation
```python
{
    "revenue_growth_yoy": {"min": 20, "max": 999},
    "peg_ratio": {"min": 0, "max": 1.0},
    "roe_percent": {"min": 15, "max": 999}
}
```

### Momentum Breakout
Technical signals confirming upward momentum
```python
{
    "signals": ["golden_cross", "rsi_bullish", "volume_surge"],
    "min_signal_strength": 70
}
```

### Financial Strength
High quality, low risk companies
```python
{
    "piotroski_score": {"min": 7, "max": 9},
    "current_ratio": {"min": 2.0, "max": 999},
    "debt_to_assets": {"min": 0, "max": 0.3},
    "roe_percent": {"min": 15, "max": 999}
}
```

---

## 11. TROUBLESHOOTING

### Pattern Returns No Results
- Check that stocks in database have the required metrics
- Verify min/max ranges are reasonable
- For technical: ensure signals have been detected (check signals table)
- For fundamental: ensure fundamental data exists (check fundamental_data table)

### Pattern Exists Error
- Pattern ID already exists in database
- Delete old pattern first or use different ID

### Invalid Signal Names
- Check signal name spelling (must match exactly)
- Use signal names from Section 2 above
- Signal names are case-sensitive (use lowercase with underscores)

### Invalid Metric Names
- Use metric names from Section 3 above
- Check spelling carefully
- Metric names are case-sensitive

---

## 12. FILE LOCATIONS

**Important Files for Pattern Implementation:**

- Pattern Logic: `/Users/raymonmudrig/AI/Screener/src/patterns/engine.py`
- Pattern Storage: `/Users/raymonmudrig/AI/Screener/src/patterns/storage.py`
- API Endpoints: `/Users/raymonmudrig/AI/Screener/src/api/web.py`
- Frontend UI: `/Users/raymonmudrig/AI/Screener/web/app.js`
- Database: `/Users/raymonmudrig/AI/Screener/database/stockCode.sqlite`

---

## Summary

Custom patterns allow users to combine:
- **Technical criteria**: Signal combinations + signal strength threshold
- **Fundamental criteria**: Multiple metric ranges
- **Sorting**: By any fundamental metric or match score
- **Categories**: Organized into value/growth/quality/health/technical/custom

The system automatically scores results (0-100), caches them (24 hours), and displays them in a user-friendly interface.
