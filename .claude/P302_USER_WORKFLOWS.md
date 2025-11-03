# User Workflows & Use Cases

**System:** IDX Stock Screener (Technical + Fundamental)
**Date:** 2025-11-01

---

## 📋 Current System Capabilities

Based on SCREENER_STRATEGY.md requirements, here's what we have:

### ✅ **Available Now**

#### Technical System
- ✅ Price data storage (OHLCV)
- ✅ 50+ technical indicators calculated
- ✅ Signal detection (trend, momentum, volatility, volume)
- ✅ Bullish/Bearish/Neutral classification
- ✅ Signal strength scoring
- ✅ Top opportunities ranking

#### Fundamental System
- ✅ Quarterly financial data (53 fields)
- ✅ 67+ calculated metrics
- ✅ 16 screening methods
- ✅ Value/Growth/Quality/Health signals
- ✅ Composite strategies (GARP, Magic Formula)
- ✅ Company size & health indicators

### ⚠️ **Gaps Identified**

- ❌ Combined technical + fundamental screening
- ❌ Interactive charts/visualization
- ❌ Custom screener presets
- ❌ Alert system
- ❌ GUI/Web interface
- ❌ Export to CSV/Excel
- ❌ Sector/industry filters

---

## 👤 User Personas & Use Cases

### 1. **Value Investor** (Warren Buffett Style)

**Goal:** Find undervalued companies with strong fundamentals

**Current Workflow:**
```bash
# Step 1: Find low P/E stocks
python3 -m src.api.cli screen-fundamental --screen-type value --criterion low-pe --limit 50

# Step 2: Filter for quality (high ROE)
python3 -m src.api.cli screen-fundamental --screen-type quality --criterion high-roe --limit 50

# Step 3: Check financial health
python3 -m src.api.cli screen-fundamental --screen-type health --criterion low-debt --limit 50

# Step 4: Deep dive into specific stock
python3 -m src.api.cli show-fundamentals BBCA --quarters 8
python3 -m src.api.cli calculate-metrics BBCA
```

**What They Get:**
- List of undervalued stocks (P/E ≤ 15)
- Quality companies (ROE ≥ 15%)
- Low debt companies (D/A ≤ 0.4)
- Detailed fundamental analysis

**Missing:**
- ❌ Combined filter (low P/E + high ROE + low debt in one command)
- ❌ Sector comparison
- ❌ Historical trends

---

### 2. **Growth Investor** (Peter Lynch Style)

**Goal:** Find fast-growing companies at reasonable prices (GARP)

**Current Workflow:**
```bash
# Step 1: Find GARP stocks (Growth at Reasonable Price)
python3 -m src.api.cli screen-fundamental --screen-type composite --criterion garp --limit 30

# Step 2: Check specific stock details
python3 -m src.api.cli calculate-metrics EMTK
python3 -m src.api.cli show-metrics EMTK

# Step 3: Look for technical confirmation
python3 -m src.api.cli detect-signals EMTK
python3 -m src.api.cli show-indicators EMTK
```

**What They Get:**
- 107 GARP stocks (PEG ≤ 1.0, Growth ≥ 10%, ROE ≥ 12%)
- Growth metrics (YoY, QoQ, CAGR)
- Technical confirmation signals

**Missing:**
- ❌ Growth consistency check
- ❌ Sector growth comparison
- ❌ Combined fundamental + technical screen

---

### 3. **Swing Trader** (Technical + Fundamental)

**Goal:** Find stocks with strong fundamentals AND bullish technical signals

**Current Workflow:**
```bash
# Step 1: Find technically strong stocks
python3 -m src.api.cli show-signals --signal-type trend --min-strength 70 --limit 50

# Step 2: For each stock, check fundamentals
python3 -m src.api.cli show-fundamentals BBCA --quarters 4
python3 -m src.api.cli calculate-metrics BBCA

# Step 3: Check specific signals
python3 -m src.api.cli detect-signals BBCA
```

**What They Get:**
- Bullish technical signals (Golden Cross, RSI, MACD)
- Fundamental health check
- Combined view (manual)

**Missing:**
- ❌ Automated combined screening
- ❌ "Strong fundamentals + Bullish signals" filter
- ❌ Chart visualization

---

### 4. **Quality Investor** (Joel Greenblatt Style)

**Goal:** Find high-quality companies at reasonable valuations

**Current Workflow:**
```bash
# Step 1: Run Magic Formula screen
python3 -m src.api.cli screen-fundamental --screen-type composite --criterion magic-formula --limit 30

# Step 2: Check Piotroski scores
python3 -m src.api.cli screen-fundamental --screen-type quality --criterion high-piotroski --limit 30

# Step 3: Analyze specific stock
python3 -m src.api.cli calculate-metrics MLBI
python3 -m src.api.cli show-metrics MLBI
```

**What They Get:**
- 103 Magic Formula stocks (ROIC ≥ 12%, EV/EBITDA ≤ 15)
- Piotroski F-Score for quality assessment
- Detailed quality metrics

**Missing:**
- ❌ Combined Magic Formula + High Piotroski
- ❌ Historical quality trends

---

### 5. **Conservative Investor** (Safety First)

**Goal:** Find financially strong, low-risk companies

**Current Workflow:**
```bash
# Step 1: Find financially strong stocks
python3 -m src.api.cli screen-fundamental --screen-type composite --criterion financial-strength --limit 30

# Step 2: Check safe Z-Score
python3 -m src.api.cli screen-fundamental --screen-type health --criterion safe-zscore --limit 30

# Step 3: Check low debt
python3 -m src.api.cli screen-fundamental --screen-type health --criterion low-debt --limit 30

# Step 4: Analyze specific stock
python3 -m src.api.cli calculate-metrics UNVR
```

**What They Get:**
- Financially strong companies (F-Score ≥ 7, Current ≥ 2.0, D/A ≤ 0.5)
- Safe Z-Score stocks (≥ 3.0)
- Low debt companies

**Missing:**
- ❌ Dividend yield screening
- ❌ Stability metrics

---

### 6. **Momentum Trader** (Technical Focus)

**Goal:** Find stocks with strong price momentum

**Current Workflow:**
```bash
# Step 1: Find strong momentum signals
python3 -m src.api.cli show-signals --signal-type momentum --min-strength 70 --limit 30

# Step 2: Check top opportunities
python3 -m src.api.cli top-opportunities --limit 20

# Step 3: Analyze specific stock
python3 -m src.api.cli show-indicators GOTO
python3 -m src.api.cli detect-signals GOTO
```

**What They Get:**
- Momentum signals (RSI, Stochastic, Williams %R)
- Top opportunities ranked by signal strength
- Detailed technical indicators

**Missing:**
- ❌ Volume confirmation
- ❌ Relative strength vs. market
- ❌ Intraday momentum

---

## 🎯 Common User Scenarios

### Scenario 1: "Find cheap, quality stocks ready to bounce"

**User Intent:** Value + Quality + Technical reversal

**Current Solution:**
```bash
# 1. Find value stocks
python3 -m src.api.cli screen-fundamental --screen-type value --criterion low-pe

# 2. Filter for quality
python3 -m src.api.cli screen-fundamental --screen-type quality --criterion high-piotroski

# 3. Check for oversold technical signals manually
python3 -m src.api.cli show-signals --signal-type momentum

# 4. Cross-reference manually
```

**Ideal Solution (Future):**
```bash
# Single command combining criteria
python3 -m src.api.cli screen-combined \
  --fundamental "low-pe,high-piotroski" \
  --technical "oversold" \
  --limit 20
```

---

### Scenario 2: "Find growth stocks with bullish momentum"

**User Intent:** Growth + Technical confirmation

**Current Solution:**
```bash
# 1. Find growth stocks
python3 -m src.api.cli screen-fundamental --screen-type growth --criterion revenue-growth

# 2. Check technical signals manually for each
python3 -m src.api.cli detect-signals <STOCK>

# 3. Filter manually
```

**Ideal Solution (Future):**
```bash
# Combined growth + bullish
python3 -m src.api.cli screen-combined \
  --fundamental "revenue-growth" \
  --technical "bullish" \
  --min-technical-strength 70 \
  --limit 20
```

---

### Scenario 3: "Monitor my watchlist daily"

**User Intent:** Track specific stocks, get alerts

**Current Solution:**
```bash
# Create a script to check multiple stocks
for stock in BBCA BMRI TLKM ASII; do
  python3 -m src.api.cli detect-signals $stock
  python3 -m src.api.cli calculate-metrics $stock
done
```

**Ideal Solution (Future):**
```bash
# Watchlist feature
python3 -m src.api.cli watchlist-add BBCA BMRI TLKM ASII
python3 -m src.api.cli watchlist-check --alert-on-signal
```

---

### Scenario 4: "Daily screening routine"

**User Intent:** Quick daily scan for opportunities

**Current Solution:**
```bash
# Morning routine
python3 -m src.api.cli top-opportunities --limit 10
python3 -m src.api.cli screen-fundamental --screen-type composite --criterion garp --limit 10
python3 -m src.api.cli show-signals --min-strength 80 --limit 10
```

**Ideal Solution (Future):**
```bash
# Saved preset
python3 -m src.api.cli run-preset "daily-scan"
# → Runs predefined screens, shows combined results
```

---

## 🔄 Complete User Journey Examples

### Example 1: Value Investor's Daily Workflow

```bash
# 8:00 AM - Data Update
python3 -m src.api.cli refresh-intraday --limit 918 --delay 0.5

# 8:30 AM - Run Screens
python3 -m src.api.cli screen-fundamental --screen-type composite --criterion magic-formula --limit 30 > magic_formula.txt

# 9:00 AM - Analyze Top Results
# From magic_formula.txt, pick top 5 stocks
python3 -m src.api.cli calculate-metrics MLBI
python3 -m src.api.cli show-fundamentals MLBI --quarters 8
python3 -m src.api.cli detect-signals MLBI

# 10:00 AM - Deep Dive
# Read quarterly reports, check news, analyze industry
# Make buy/sell decision

# 4:00 PM - Evening Update
python3 -m src.api.cli refresh-intraday --skip-price-update
# → Recalculate indicators and signals only
```

---

### Example 2: Growth Investor's Weekly Workflow

```bash
# Monday - Find New Opportunities
python3 -m src.api.cli screen-fundamental --screen-type composite --criterion garp --limit 50
python3 -m src.api.cli screen-fundamental --screen-type growth --criterion accelerating --limit 30

# Tuesday-Thursday - Research
# Deep dive into top 10 stocks from Monday's screens
for stock in EMTK ARCI BUKA VICO TPIA; do
  echo "=== $stock ==="
  python3 -m src.api.cli calculate-metrics $stock
  python3 -m src.api.cli show-metrics $stock
  python3 -m src.api.cli detect-signals $stock
done

# Friday - Update & Review
python3 -m src.api.cli update-all-fundamentals --limit 50 --delay 1.0
python3 -m src.api.cli calculate-all-metrics --limit 50
```

---

### Example 3: Swing Trader's Entry Setup

```bash
# Step 1: Find technically strong stocks
python3 -m src.api.cli show-signals --signal-type trend --min-strength 70 --limit 30

# Step 2: Filter for fundamental quality
# For each stock from Step 1:
python3 -m src.api.cli calculate-metrics BBCA
# → Check: ROE > 15%, P/E < 20, Debt/Assets < 0.5

# Step 3: Technical confirmation
python3 -m src.api.cli show-indicators BBCA
# → Confirm: RSI 50-70, MACD positive, above EMA 20

# Step 4: Entry decision
# If all criteria met:
# - Strong fundamentals ✓
# - Bullish trend ✓
# - Good entry point ✓
# → Place buy order

# Step 5: Set exit
# - Stop loss: Below recent support (use chart)
# - Target: Based on resistance levels
```

---

## 📊 Recommended Enhancement: Combined Screener

### New Module: `src/screener/combined.py`

**Purpose:** Combine technical + fundamental screening in one operation

**Example Usage:**
```bash
# Combined screen: Value + Bullish
python3 -m src.api.cli screen-combined \
  --fundamental-criteria "low-pe,high-roe" \
  --technical-criteria "golden-cross,rsi-bullish" \
  --min-fundamental-score 70 \
  --min-technical-strength 70 \
  --limit 20

# Output:
# Stock | P/E | ROE% | Technical Signals | Combined Score
# BBCA  | 8.5 | 21.3 | Golden Cross, RSI(65) | 85/100
# BMRI  | 7.2 | 18.7 | Bullish MACD, RSI(58) | 82/100
```

**Scoring System:**
- Fundamental Score (0-100): Based on criteria met
- Technical Score (0-100): Average signal strength
- Combined Score: Weighted average (e.g., 60% fundamental, 40% technical)

---

## 🎨 GUI Mockup Alignment

From SCREENER_STRATEGY.md mockup:

```
Screener Name: "Cheap big company on reversal"

Filters:
  Technical:
    [X] Golden Cross
    [ ] Death Cross
    [X] RSI Oversold

  Fundamental:
    1,000,000 < Market Cap < 100,000,000
    0.5 < P/E < 2.8
    0.5 < P/B < 2.8

Results:
  Stock | Signals & Metrics
  BBCA  | RSI: Bullish 88%, Golden Cross, P/E: 2.5, Market Cap: 5.3B
```

**How to achieve this with current CLI:**

```bash
# 1. Technical filter (manual combination)
python3 -m src.api.cli show-signals --signal-type trend --limit 100 | grep "Golden Cross"

# 2. Fundamental filter
python3 -m src.api.cli screen-fundamental --screen-type value --criterion low-pe

# 3. Manual cross-reference to find stocks meeting both criteria
```

**Future implementation needed:**
- Combined screener module
- Custom filter builder
- Preset saving/loading
- Result caching

---

## 📈 Feature Roadmap

### Priority 1: Core Integration
1. **Combined Screener** - Technical + Fundamental in one command
2. **Custom Presets** - Save and load screening criteria
3. **Watchlist** - Track specific stocks, daily updates
4. **Alert System** - Notify when stocks meet criteria

### Priority 2: Usability
5. **CSV Export** - Export screening results
6. **Batch Analysis** - Analyze multiple stocks at once
7. **Comparison View** - Compare stocks side-by-side
8. **Historical Screening** - Backtest screening strategies

### Priority 3: Advanced
9. **Sector Filters** - Screen within specific sectors
10. **Relative Strength** - Compare vs. sector/market
11. **Custom Formulas** - User-defined screening formulas
12. **GUI/Web Interface** - Visual screening tool

---

## 💡 Quick Reference: Command Combinations

### For Value Investors
```bash
# Step 1: Find undervalued quality stocks
python3 -m src.api.cli screen-fundamental --screen-type composite --criterion magic-formula --limit 30

# Step 2: Check for additional value metrics
python3 -m src.api.cli screen-fundamental --screen-type value --criterion low-pb --limit 30

# Step 3: Verify financial health
python3 -m src.api.cli screen-fundamental --screen-type health --criterion safe-zscore --limit 30
```

### For Growth Investors
```bash
# Step 1: Find GARP stocks
python3 -m src.api.cli screen-fundamental --screen-type composite --criterion garp --limit 30

# Step 2: Confirm with growth metrics
python3 -m src.api.cli screen-fundamental --screen-type growth --criterion revenue-growth --limit 30

# Step 3: Check technical momentum
python3 -m src.api.cli show-signals --signal-type momentum --min-strength 70 --limit 30
```

### For Swing Traders
```bash
# Step 1: Find bullish technical setups
python3 -m src.api.cli top-opportunities --limit 20

# Step 2: Filter for fundamental quality
python3 -m src.api.cli screen-fundamental --screen-type quality --criterion high-roe --limit 30

# Step 3: Cross-check (manual for now)
```

---

## ✅ Action Items

### For Users (Current System)
1. ✅ Use separate commands for technical and fundamental screening
2. ✅ Manually cross-reference results
3. ✅ Create shell scripts for routine workflows
4. ✅ Use `grep`, `awk` for filtering CLI output

### For Development (Future)
1. ⏳ Build combined screener module
2. ⏳ Implement preset system
3. ⏳ Add watchlist feature
4. ⏳ Create alert system
5. ⏳ Build CSV export
6. ⏳ Develop GUI/Web interface

---

**Document Status:** Complete
**Last Updated:** 2025-11-01
**Next Review:** After user feedback
