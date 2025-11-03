# Fundamental Screener Implementation Plan

## Overview

Build a comprehensive fundamental analysis system to complement the existing technical screener, enabling value, growth, quality, and multi-factor screening strategies.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STOCK SCREENER SYSTEM                    │
├─────────────────────────────────────────────────────────────┤
│  TECHNICAL ANALYSIS              FUNDAMENTAL ANALYSIS       │
│  ├── Price Data (OHLCV)          ├── Financial Statements   │
│  ├── 40+ Indicators              ├── Ratios & Metrics       │
│  ├── 25+ Signals                 ├── Growth Calculations    │
│  └── Signal Strength             └── Quality Scores         │
├─────────────────────────────────────────────────────────────┤
│              COMBINED SCREENING ENGINE                      │
│  ├── Multi-Factor Scoring                                   │
│  ├── Value + Growth + Quality + Momentum                    │
│  └── Custom Screening Strategies                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Database & Data Infrastructure

### 1.1 Database Schema

**New Tables:**

```sql
-- Fundamental data (quarterly reports)
CREATE TABLE fundamental_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,  -- 1-4
    report_date DATE NOT NULL,

    -- Stock Info
    close_price REAL,
    par_value REAL,
    shares_outstanding REAL,

    -- Balance Sheet - Assets
    receivables REAL,
    inventories REAL,
    current_assets REAL,
    fixed_assets REAL,
    other_assets REAL,
    total_assets REAL,
    non_current_assets REAL,

    -- Balance Sheet - Liabilities
    current_liabilities REAL,
    long_term_liabilities REAL,
    total_liabilities REAL,

    -- Balance Sheet - Equity
    retained_earnings REAL,
    total_equity REAL,
    minority_interest REAL,

    -- Income Statement
    revenue REAL,
    cost_of_goods_sold REAL,
    gross_profit REAL,
    operating_profit REAL,
    other_income REAL,
    earnings_before_tax REAL,
    tax REAL,
    net_income REAL,

    -- Cash Flow
    cf_operating REAL,
    cf_investing REAL,
    cf_financing REAL,
    net_cash_increase REAL,
    cash_begin REAL,
    cash_end REAL,

    -- Pre-calculated Ratios
    eps REAL,
    book_value REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    debt_equity_ratio REAL,
    roa_percent REAL,
    roe_percent REAL,
    npm_percent REAL,
    opm_percent REAL,
    gross_margin_percent REAL,
    asset_turnover REAL,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stock_id, year, quarter),
    FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
);

-- Calculated fundamental metrics
CREATE TABLE fundamental_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    metric_name TEXT NOT NULL,  -- e.g., 'revenue_growth_yoy', 'current_ratio'
    value REAL,
    metadata TEXT,  -- JSON for additional info
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stock_id, year, quarter, metric_name),
    FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
);

-- TTM (Trailing 12 Months) metrics
CREATE TABLE ttm_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    as_of_date DATE NOT NULL,  -- Date of latest quarter

    -- TTM Income Statement
    ttm_revenue REAL,
    ttm_gross_profit REAL,
    ttm_operating_profit REAL,
    ttm_net_income REAL,
    ttm_eps REAL,

    -- TTM Margins
    ttm_gross_margin REAL,
    ttm_operating_margin REAL,
    ttm_net_margin REAL,

    -- TTM Cash Flow
    ttm_cf_operating REAL,
    ttm_cf_investing REAL,
    ttm_cf_financing REAL,

    -- TTM Ratios
    ttm_roe REAL,
    ttm_roa REAL,
    ttm_roic REAL,

    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stock_id, as_of_date),
    FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
);

-- Fundamental signals/scores
CREATE TABLE fundamental_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,  -- 'value', 'growth', 'quality', 'health'
    signal_name TEXT NOT NULL,
    detected_date DATE NOT NULL,
    score REAL,  -- 0-100
    details TEXT,  -- JSON with criteria met
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
);

-- Screening results cache
CREATE TABLE screening_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_name TEXT NOT NULL,
    stock_id TEXT NOT NULL,
    rank INTEGER,
    score REAL,
    criteria_met TEXT,  -- JSON
    screened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
);

-- Indexes
CREATE INDEX idx_fundamental_data_stock ON fundamental_data(stock_id, year, quarter);
CREATE INDEX idx_fundamental_metrics_stock ON fundamental_metrics(stock_id, metric_name);
CREATE INDEX idx_ttm_metrics_stock ON ttm_metrics(stock_id, as_of_date);
CREATE INDEX idx_fundamental_signals_stock ON fundamental_signals(stock_id, signal_type, is_active);
CREATE INDEX idx_screening_results_screen ON screening_results(screen_name, rank);
```

### 1.2 Data Fetcher

**Module:** `src/data/fundamental_fetcher.py`

```python
class FundamentalDataFetcher:
    """Fetch quarterly fundamental data from IDX API"""

    def fetch_quarterly_data(stock_id: str, year: int, quarter: int)
    def fetch_latest_quarter(stock_id: str)
    def fetch_multiple_quarters(stock_id: str, num_quarters: int = 8)
    def fetch_all_stocks_latest()
```

### 1.3 Data Storage

**Module:** `src/data/fundamental_storage.py`

```python
class FundamentalDataStorage:
    """Store and retrieve fundamental data"""

    def store_quarterly_data(stock_id, year, quarter, data)
    def get_quarterly_data(stock_id, year, quarter)
    def get_latest_quarters(stock_id, num_quarters)
    def update_all_stocks()
```

**Estimated Time:** 1 day

---

## Phase 2: Fundamental Metrics Calculation

### 2.1 Growth Calculators

**Module:** `src/fundamentals/growth.py`

```python
class GrowthCalculator:
    """Calculate growth metrics"""

    # Revenue Growth
    def revenue_growth_yoy(current_q, previous_year_q)
    def revenue_growth_qoq(current_q, previous_q)
    def revenue_cagr(quarters)

    # Earnings Growth
    def eps_growth_yoy()
    def eps_growth_qoq()
    def net_income_growth()

    # Other Growth
    def asset_growth()
    def equity_growth()
    def cash_flow_growth()
```

### 2.2 Ratio Calculators

**Module:** `src/fundamentals/ratios.py`

```python
class RatioCalculator:
    """Calculate financial ratios"""

    # Liquidity
    def current_ratio()
    def quick_ratio()
    def cash_ratio()
    def working_capital()

    # Leverage
    def debt_to_assets()
    def equity_ratio()
    def financial_leverage()

    # Efficiency
    def inventory_turnover()
    def receivables_turnover()
    def payables_turnover()

    # Valuation
    def price_to_sales()
    def price_to_cash_flow()
    def ev_to_ebitda()
    def market_cap()
    def enterprise_value()
```

### 2.3 Quality Scores

**Module:** `src/fundamentals/quality.py`

```python
class QualityScorer:
    """Calculate quality scores"""

    def piotroski_f_score()  # 9-point scale
    def altman_z_score()     # Bankruptcy prediction
    def cash_quality_score() # OCF/Net Income
    def margin_stability()
    def roe_consistency()
```

### 2.4 TTM Calculator

**Module:** `src/fundamentals/ttm.py`

```python
class TTMCalculator:
    """Calculate Trailing 12 Months metrics"""

    def calculate_ttm_metrics(stock_id, as_of_quarter)
    def ttm_revenue(last_4_quarters)
    def ttm_net_income(last_4_quarters)
    def ttm_cash_flow(last_4_quarters)
    def ttm_margins(last_4_quarters)
```

**Estimated Time:** 2 days

---

## Phase 3: Fundamental Screening Signals

### 3.1 Value Signals

**Module:** `src/fundamentals/signals/value_signals.py`

```python
class ValueSignals:
    """Detect value opportunities"""

    # Low Valuation
    def low_pe_signal()        # P/E < 15
    def low_pb_signal()        # P/B < 1.5
    def low_ps_signal()        # P/S < 2
    def high_dividend_yield()  # Yield > 4%

    # Deep Value
    def deep_value_combo()     # P/B < 1 + P/E < 12 + Yield > 3%
    def graham_number()        # Benjamin Graham valuation
    def net_net_working_cap()  # NCAV strategy
```

### 3.2 Growth Signals

**Module:** `src/fundamentals/signals/growth_signals.py`

```python
class GrowthSignals:
    """Detect growth opportunities"""

    # Revenue Growth
    def high_revenue_growth()     # >20% YoY
    def accelerating_growth()     # Growth rate increasing

    # Earnings Growth
    def high_eps_growth()         # >25% YoY
    def consistent_growth()       # Positive for 4+ quarters

    # Combined
    def peg_ratio_attractive()    # PEG < 1
    def margin_expansion()        # Margins improving
```

### 3.3 Quality Signals

**Module:** `src/fundamentals/signals/quality_signals.py`

```python
class QualitySignals:
    """Detect high-quality companies"""

    # Profitability
    def high_roe()            # ROE > 15%
    def high_roic()           # ROIC > 12%
    def high_margins()        # Net margin > 15%

    # Consistency
    def consistent_profits()  # Profitable 8+ quarters
    def stable_margins()      # Low margin volatility

    # Composite
    def piotroski_high()      # F-Score >= 7
    def quality_combo()       # ROE + Margins + Low Debt
```

### 3.4 Financial Health Signals

**Module:** `src/fundamentals/signals/health_signals.py`

```python
class HealthSignals:
    """Detect financially healthy companies"""

    # Liquidity
    def strong_liquidity()    # Current ratio > 2
    def positive_cash_flow()  # OCF > 0

    # Solvency
    def low_debt()            # D/E < 0.5
    def high_interest_cover() # EBIT/Interest > 5x

    # Composite
    def altman_safe()         # Z-Score > 3
    def financial_fortress()  # Multiple criteria
```

### 3.5 Composite Screening

**Module:** `src/fundamentals/screener.py`

```python
class FundamentalScreener:
    """Multi-factor fundamental screening"""

    # Pre-built Screens
    def value_screen()
    def growth_screen()
    def quality_screen()
    def dividend_screen()
    def combined_screen()

    # Custom Screening
    def custom_screen(criteria)
    def rank_stocks(factors, weights)
    def filter_universe(filters)
```

**Estimated Time:** 2 days

---

## Phase 4: Integration & Enhancement

### 4.1 Combined Technical + Fundamental

**Module:** `src/screening/combined_screener.py`

```python
class CombinedScreener:
    """Combine technical and fundamental signals"""

    def quality_with_momentum()
    # High ROE + Low P/E + MACD Bullish + RSI > 50

    def value_with_reversal()
    # Low P/B + Improving margins + Golden Cross

    def growth_with_breakout()
    # High revenue growth + Volume breakout + BB breakout

    def multi_factor_score()
    # Weighted combination of all factors
```

### 4.2 CLI Commands

**Updates to:** `src/api/cli.py`

```bash
# Fundamental data management
python3 -m src.api.cli update-fundamentals BBCA
python3 -m src.api.cli update-all-fundamentals
python3 -m src.api.cli show-fundamentals BBCA

# Fundamental screening
python3 -m src.api.cli screen-value --min-score 70
python3 -m src.api.cli screen-growth --min-growth 20
python3 -m src.api.cli screen-quality --min-roe 15
python3 -m src.api.cli screen-combined --factors value,growth,quality

# Comparison
python3 -m src.api.cli compare BBCA BMRI TLKM
python3 -m src.api.cli rank-sector BANKING --by roe
```

### 4.3 Intraday Refresh Integration

**Update:** `refresh-intraday` command

```python
def refresh_intraday():
    # Step 1: Update prices
    # Step 2: Calculate technical indicators
    # Step 3: Detect technical signals
    # Step 4: Update fundamentals (quarterly check)  ← NEW
    # Step 5: Recalculate fundamental metrics        ← NEW
    # Step 6: Run combined screening                 ← NEW
```

**Estimated Time:** 1 day

---

## Implementation Schedule

### Week 1: Core Infrastructure
- **Day 1:** Database schema + fundamental fetcher
- **Day 2:** Data storage + batch update scripts
- **Day 3:** Growth & ratio calculators

### Week 2: Screening System
- **Day 4:** Quality scores + TTM metrics
- **Day 5:** Value & growth signals
- **Day 6:** Quality & health signals
- **Day 7:** Composite screener + CLI commands

**Total Estimated Time:** 7 days

---

## Deliverables

### Code Modules
1. ✅ `src/data/fundamental_fetcher.py` - Data fetcher
2. ✅ `src/data/fundamental_storage.py` - Storage layer
3. ✅ `src/fundamentals/growth.py` - Growth calculations
4. ✅ `src/fundamentals/ratios.py` - Ratio calculations
5. ✅ `src/fundamentals/quality.py` - Quality scores
6. ✅ `src/fundamentals/ttm.py` - TTM calculations
7. ✅ `src/fundamentals/signals/value_signals.py` - Value signals
8. ✅ `src/fundamentals/signals/growth_signals.py` - Growth signals
9. ✅ `src/fundamentals/signals/quality_signals.py` - Quality signals
10. ✅ `src/fundamentals/signals/health_signals.py` - Health signals
11. ✅ `src/fundamentals/screener.py` - Main screener
12. ✅ `src/screening/combined_screener.py` - Technical + Fundamental

### Database
- ✅ 5 new tables for fundamental data
- ✅ Indexes for performance
- ✅ Foreign key relationships

### CLI Commands
- ✅ 15+ new CLI commands for fundamental screening
- ✅ Integration with existing technical screener

### Documentation
- ✅ `FUNDAMENTAL_DATA_EVALUATION.md` - Data source analysis
- ✅ `FUNDAMENTAL_IMPLEMENTATION_PLAN.md` - This document
- ✅ `FUNDAMENTAL_COMPLETE.md` - Completion report (after Phase 4)
- ✅ `SCREENING_STRATEGIES.md` - Strategy guide

---

## Success Metrics

### Data Coverage
- ✅ 8+ quarters of fundamental data per stock
- ✅ 1,400+ stocks covered
- ✅ <1% data fetch failure rate

### Metrics Calculated
- ✅ 50+ fundamental metrics per stock
- ✅ Growth metrics (YoY, QoQ, TTM)
- ✅ All major ratios (liquidity, leverage, efficiency)
- ✅ Quality scores (Piotroski, Altman Z)

### Screening Performance
- ✅ <5 seconds for single-factor screen
- ✅ <15 seconds for multi-factor screen
- ✅ Rank 1,400+ stocks by composite score

### User Features
- ✅ Pre-built screening strategies
- ✅ Custom criteria builder
- ✅ Combined technical + fundamental
- ✅ Sector/peer comparison
- ✅ Automated refresh integration

---

## Pre-built Screening Strategies

### 1. Classic Value
```python
criteria = {
    'pe_ratio': {'max': 15},
    'pb_ratio': {'max': 1.5},
    'debt_equity': {'max': 0.5},
    'dividend_yield': {'min': 3},
    'current_ratio': {'min': 2}
}
```

### 2. Quality Growth
```python
criteria = {
    'roe': {'min': 15},
    'revenue_growth_yoy': {'min': 15},
    'net_margin': {'min': 10},
    'piotroski_score': {'min': 7},
    'debt_equity': {'max': 1}
}
```

### 3. Undervalued Growth
```python
criteria = {
    'peg_ratio': {'max': 1},
    'revenue_growth_yoy': {'min': 20},
    'eps_growth_yoy': {'min': 25},
    'pb_ratio': {'max': 3}
}
```

### 4. Dividend Aristocrats
```python
criteria = {
    'dividend_yield': {'min': 4},
    'payout_ratio': {'max': 60},
    'consecutive_dividends': {'min': 5},
    'fcf_coverage': {'min': 1.5}
}
```

### 5. Financial Fortress
```python
criteria = {
    'current_ratio': {'min': 2},
    'debt_equity': {'max': 0.3},
    'altman_z_score': {'min': 3},
    'interest_coverage': {'min': 5},
    'roe': {'min': 12}
}
```

---

## Risk Mitigation

### Data Quality
- ✅ Validate data ranges
- ✅ Handle missing quarters
- ✅ Detect anomalies
- ✅ Audit trail for calculations

### Performance
- ✅ Batch processing for efficiency
- ✅ Caching for TTM calculations
- ✅ Indexed database queries
- ✅ Incremental updates

### User Experience
- ✅ Progress indicators
- ✅ Error handling
- ✅ Clear documentation
- ✅ Example strategies

---

## Future Enhancements (Phase 5+)

1. **Sector Analysis**
   - Industry averages
   - Peer comparison
   - Relative valuation

2. **Forecasting**
   - Trend projection
   - Growth sustainability
   - Scenario analysis

3. **Alerts**
   - Value opportunities
   - Growth accelerations
   - Quality deterioration

4. **Dashboard**
   - Visual screening
   - Interactive charts
   - Portfolio tracking

---

**Plan Version:** 1.0
**Created:** 2025-10-31
**Status:** READY FOR IMPLEMENTATION ✅
**Estimated Completion:** 7 days
