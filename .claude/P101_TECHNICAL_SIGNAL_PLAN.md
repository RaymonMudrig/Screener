# Stock Screener System Plan

## Overview
A comprehensive stock screener system for Indonesian Stock Exchange (IDX) data, focusing on technical signal detection and analysis based on price data.

---

## 1. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                     STOCK SCREENER SYSTEM                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐      ┌──────────────────┐              │
│  │ Data Ingestion  │─────▶│  SQLite Database │              │
│  │    Pipeline     │      │  (stockCode.db)  │              │
│  └─────────────────┘      └──────────────────┘              │
│         │                           │                       │
│         │                           ▼                       │
│         │                  ┌──────────────────┐             │
│         └─────────────────▶│   Calculation    │             │
│                            │     Engine       │             │
│                            │  (Indicators)    │             │
│                            └──────────────────┘             │
│                                     │                       │
│                                     ▼                       │
│                            ┌──────────────────┐             │
│                            │   Screening &    │             │
│                            │  Signal Engine   │             │
│                            └──────────────────┘             │
│                                     │                       │
│                                     ▼                       │
│                            ┌──────────────────┐             │
│                            │   API / CLI      │             │
│                            │   Interface      │             │
│                            └──────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Layers

1. **Data Ingestion Pipeline**: Fetches stock list and price data from IDX sources
2. **SQLite Database**: Persistent storage for stocks, prices, indicators, and signals
3. **Calculation Engine**: Computes technical indicators from price data
4. **Screening & Signal Engine**: Detects trading signals and patterns
5. **API/CLI Interface**: User interface for querying and screening stocks

---

## 2. DATABASE SCHEMA (SQLite)

### Tables

#### stocks
```sql
-- Stock master data
CREATE TABLE stocks (
    stock_id TEXT PRIMARY KEY,
    stock_code TEXT NOT NULL,
    stock_name TEXT,
    sector TEXT,
    subsector TEXT,
    last_updated TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### price_data
```sql
-- Price data (OHLCV)
CREATE TABLE price_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
    UNIQUE(stock_id, date)
);
```

#### indicators
```sql
-- Pre-calculated indicators (for performance)
CREATE TABLE indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    date DATE NOT NULL,
    indicator_name TEXT NOT NULL,
    value REAL,
    metadata TEXT, -- JSON for additional data
    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
    UNIQUE(stock_id, date, indicator_name)
);
```

#### signals
```sql
-- Detected signals
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    signal_name TEXT NOT NULL,
    detected_date DATE NOT NULL,
    strength REAL, -- 0-100 score
    metadata TEXT, -- JSON with signal details
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
);
```

### Indexes
```sql
-- Indexes for performance
CREATE INDEX idx_price_stock_date ON price_data(stock_id, date DESC);
CREATE INDEX idx_indicators_stock_date ON indicators(stock_id, date DESC);
CREATE INDEX idx_signals_date ON signals(detected_date DESC);
CREATE INDEX idx_signals_active ON signals(is_active, signal_type);
```

---

## 3. DATA INGESTION PIPELINE

### Data Sources

#### Stock List
- **URL**: `https://139.255.96.106:1443/GetAllStock`
- **Purpose**: Get list of all available stocks
- **Note**: Self-signed SSL certificate

#### Price Data
- **URL**: `https://idxmobile.co.id//Data/hsx?stockID={stockID}&code={startDate}-{endDate}`
- **Parameters**:
  - `stockID`: Stock code from stock list
  - Date format: `m/d/yyyy`
- **Example**: `https://idxmobile.co.id//Data/hsx?stockID=BBCA&code=6/18/2024-7/10/2025`

### Components

#### 1. Stock List Fetcher
- Fetch from: `https://139.255.96.106:1443/GetAllStock`
- Update stocks table with latest listing
- Handle SSL certificate issues (self-signed cert)
- Mark inactive stocks

#### 2. Price Data Fetcher
- Fetch from IDX mobile API
- Batch processing for multiple stocks
- Incremental updates (only fetch missing dates)
- Rate limiting and error handling
- Retry logic for failed requests

#### 3. Data Validation
- Check for data quality issues
- Handle missing data, gaps, outliers
- Validate OHLC relationships (High >= Open/Close/Low, etc.)
- Data normalization
- Corporate action detection

### Workflow
```
1. Fetch stock list → Update stocks table
2. For each active stock:
   - Determine date range needed
   - Fetch price data
   - Validate and clean data
   - Insert/update price_data table
3. Log progress and errors
4. Update last_updated timestamp
```

---

## 4. TECHNICAL INDICATOR CALCULATION ENGINE

### Priority Indicators (Phase 1)

#### Trend Following
- **Simple Moving Averages (SMA)**: 20, 50, 200
- **Exponential Moving Averages (EMA)**: 12, 26
- **MACD** (12, 26, 9): Signal line and histogram
- **ADX** (14): Trend strength
- **Parabolic SAR**: Stop and reverse

#### Momentum/Oscillators
- **RSI** (14): Relative Strength Index
- **Stochastic** (14, 3, 3): %K and %D
- **Williams %R** (14): Momentum indicator
- **CCI** (20): Commodity Channel Index
- **ROC** (12): Rate of Change

#### Volatility
- **Bollinger Bands** (20, 2): Upper, middle, lower bands
- **ATR** (14): Average True Range
- **Bollinger Band Width**: Volatility measure
- **%B indicator**: Position within bands

#### Volume
- **Volume SMA** (20): Average volume
- **OBV**: On Balance Volume
- **Volume Rate of Change**: Volume momentum
- **VWAP**: Volume Weighted Average Price

### Architecture Example

```python
class IndicatorCalculator:
    """Calculate technical indicators for stock data"""

    def __init__(self, db_connection):
        self.db = db_connection

    def calculate_for_stock(self, stock_id, start_date, end_date):
        """Calculate all indicators for a stock"""
        # Fetch price data
        # Calculate all indicators
        # Store in indicators table
        pass

    def calculate_sma(self, prices, period):
        """Calculate Simple Moving Average"""
        pass

    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        pass

    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD, signal line, and histogram"""
        pass

    def calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        pass

    def calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        pass

    def calculate_atr(self, high, low, close, period=14):
        """Calculate Average True Range"""
        pass

    def calculate_obv(self, close, volume):
        """Calculate On Balance Volume"""
        pass
```

---

## 5. SIGNAL DETECTION ENGINE

### Signal Categories (Phase 1 Priority)

#### 1. Trend Signals
- **Golden Cross**: SMA50 crosses above SMA200 (bullish)
- **Death Cross**: SMA50 crosses below SMA200 (bearish)
- **Fast Cross**: SMA20 crosses SMA50
- **MACD Crossover**: MACD line crosses signal line
- **MACD Histogram Reversal**: Histogram changes sign

#### 2. Momentum Signals
- **RSI Oversold**: RSI < 30 (potential reversal up)
- **RSI Overbought**: RSI > 70 (potential reversal down)
- **RSI Midline Cross**: RSI crosses 50 level
- **Stochastic Extremes**: %K in overbought/oversold zones
- **Bullish/Bearish Divergences**: Price vs indicator mismatch

#### 3. Volatility Signals
- **Bollinger Band Squeeze**: Bands narrow (low volatility, breakout pending)
- **Bollinger Band Breakout**: Price breaks above/below bands
- **ATR Expansion**: Volatility increasing
- **ATR Contraction**: Volatility decreasing (calm before storm)

#### 4. Volume Signals
- **Volume Breakout**: Volume > 2x average
- **OBV Divergence**: OBV diverges from price
- **Climax Volume**: Extremely high volume (potential exhaustion)
- **Volume Confirmation**: Strong volume on price moves

#### 5. Pattern Signals (Basic)
- **52-Week High/Low Breakout**: Price breaks yearly extremes
- **Support/Resistance Breaks**: Key level violations
- **Gap Patterns**: Gap up/down, gap fill

### Signal Scoring System

```python
class SignalDetector:
    """Detect trading signals from indicators"""

    def detect_signals(self, stock_id, date):
        """Detect all active signals for a stock"""
        signals = []

        # Detect each signal type
        # Calculate signal strength (0-100)
        # Store in signals table

        return signals

    def calculate_signal_strength(self, signal_data):
        """
        Calculate signal strength (0-100) based on:
        - Volume confirmation
        - Multiple indicator alignment
        - Trend strength
        - Historical reliability
        - Distance from threshold
        """
        pass

    def detect_golden_cross(self, stock_id, date):
        """Detect Golden Cross signal"""
        pass

    def detect_rsi_extremes(self, stock_id, date):
        """Detect RSI overbought/oversold"""
        pass

    def detect_macd_crossover(self, stock_id, date):
        """Detect MACD crossover"""
        pass

    def detect_bollinger_squeeze(self, stock_id, date):
        """Detect Bollinger Band squeeze"""
        pass

    def detect_volume_breakout(self, stock_id, date):
        """Detect volume breakout"""
        pass
```

### Signal Strength Factors
- **Volume Confirmation**: +20 points if volume confirms
- **Multiple Indicator Alignment**: +15 points per aligned indicator
- **Trend Strength**: +10 points if ADX > 25
- **Historical Reliability**: +10 points based on backtest
- **Distance from Threshold**: 0-25 points based on conviction

---

## 6. SCREENING & FILTERING SYSTEM

### Screener Interface

```python
class Screener:
    """Screen stocks based on signals and criteria"""

    def screen_by_signal(self, signal_type, min_strength=50):
        """Return stocks with active signals of given type"""
        pass

    def screen_by_combination(self, conditions):
        """
        Screen by multiple conditions
        Example: Golden Cross + Volume Breakout + RSI > 50
        """
        pass

    def screen_by_sector(self, sector, signal_type):
        """Filter by sector/subsector"""
        pass

    def get_top_opportunities(self, limit=20):
        """Get top-ranked stocks by composite signal strength"""
        pass

    def screen_by_custom_criteria(self, criteria_dict):
        """Flexible screening with custom criteria"""
        pass
```

### Pre-Built Screening Strategies

#### Conservative Strategy
- Golden Cross + Volume confirmation + RSI > 50
- Trend + Momentum + Volume alignment
- ADX > 25 (strong trend)

#### Aggressive Strategy
- Fast MA cross + Volatility breakout + Volume spike
- Multiple oscillator extremes + Divergence
- High signal strength (>75)

#### Balanced Strategy
- Price pattern + MA trend + Volume + Momentum oscillator
- Medium signal strength (50-75)
- Sector rotation consideration

---

## 7. TECHNOLOGY STACK

### Core Technologies
- **Language**: Python 3.10+
- **Database**: SQLite3
- **Data Processing**: Pandas, NumPy
- **Technical Indicators**: TA-Lib or pandas-ta
- **HTTP Requests**: aiohttp (async) or requests
- **CLI Framework**: Click or argparse
- **Configuration**: YAML or TOML

### Optional Enhancements
- **Web Framework**: FastAPI for REST API
- **Frontend**: Streamlit or Dash for dashboard
- **Testing**: pytest
- **Logging**: loguru
- **Task Scheduling**: APScheduler

---

## 8. PROJECT STRUCTURE

```
stock-screener/
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetcher.py          # Data ingestion
│   │   ├── validator.py        # Data validation
│   │   └── storage.py          # Database operations
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── trend.py            # Trend indicators
│   │   ├── momentum.py         # Momentum indicators
│   │   ├── volatility.py       # Volatility indicators
│   │   └── volume.py           # Volume indicators
│   ├── signals/
│   │   ├── __init__.py
│   │   ├── detector.py         # Signal detection
│   │   ├── scorer.py           # Signal strength scoring
│   │   └── filters.py          # Signal filtering
│   ├── screener/
│   │   ├── __init__.py
│   │   ├── engine.py           # Screening logic
│   │   └── strategies.py       # Pre-built strategies
│   ├── api/
│   │   ├── __init__.py
│   │   ├── rest_api.py         # REST API (optional)
│   │   └── cli.py              # Command line interface
│   └── utils/
│       ├── __init__.py
│       ├── config.py           # Configuration
│       ├── logger.py           # Logging
│       └── db.py               # Database utilities
├── database/
│   └── stockCode.sqlite
├── config/
│   ├── settings.yaml
│   └── indicators.yaml
├── tests/
│   ├── __init__.py
│   ├── test_data.py
│   ├── test_indicators.py
│   ├── test_signals.py
│   └── test_screener.py
├── scripts/
│   ├── init_db.py
│   ├── fetch_data.py
│   └── calculate_indicators.py
├── requirements.txt
├── setup.py
├── README.md
└── .gitignore
```

---

## 9. IMPLEMENTATION PHASES

### Phase 1: Foundation (Week 1-2)
**Goal**: Basic data collection and storage

- [ ] Database setup and schema creation
- [ ] Data ingestion pipeline for stock list
- [ ] Data ingestion pipeline for price data
- [ ] Basic price data storage and validation
- [ ] Core technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)
- [ ] Database indexes and optimization

**Deliverables**:
- Working database with price data for all IDX stocks
- 10-15 core indicators calculated and stored

---

### Phase 2: Signal Detection (Week 3-4)
**Goal**: Detect and score trading signals

- [ ] Implement 10-15 key signal detectors
- [ ] Signal strength scoring system
- [ ] Signal storage and management
- [ ] Basic screening functionality
- [ ] CLI interface for querying signals
- [ ] Data update scheduler

**Deliverables**:
- Signal detection for all major patterns
- CLI tool to screen stocks by signals
- Automated daily updates

---

### Phase 3: Advanced Features (Week 5-6)
**Goal**: Enhanced analysis capabilities

- [ ] Additional indicators (30+ total)
- [ ] Multi-timeframe analysis
- [ ] Pattern recognition (candlestick, chart patterns)
- [ ] Sector/market analysis
- [ ] Performance optimization
- [ ] Backtesting framework (basic)

**Deliverables**:
- Comprehensive indicator library
- Pattern recognition system
- Performance metrics for signals

---

### Phase 4: Enhancement (Week 7+)
**Goal**: Production-ready system

- [ ] Advanced backtesting framework
- [ ] Signal quality metrics and validation
- [ ] Advanced composite strategies
- [ ] Web dashboard (optional)
- [ ] Alert system (email/notifications)
- [ ] API documentation
- [ ] User documentation

**Deliverables**:
- Production-ready screener
- Web interface (optional)
- Complete documentation

---

## 10. KEY CONSIDERATIONS

### Performance Optimization
- Pre-calculate indicators during off-hours
- Use database indexes on frequently queried columns
- Batch processing for multiple stocks
- Caching for common queries
- Lazy loading for large datasets
- Parallel processing where possible

### Data Quality
- Handle market holidays and gaps
- Validate data integrity (OHLC relationships)
- Handle corporate actions (splits, dividends)
- Error logging and alerts
- Data reconciliation checks
- Outlier detection and handling

### Scalability
- Design for 800+ Indonesian stocks
- Incremental updates only (don't re-fetch all data)
- Async data fetching for speed
- Efficient SQL queries with proper indexes
- Pagination for large result sets
- Archive old signals periodically

### Reliability
- Retry logic for API calls with exponential backoff
- Data backup strategy
- Graceful error handling
- Comprehensive logging and monitoring
- Health checks for data freshness
- Fallback mechanisms for API failures

### Security
- Handle SSL certificate issues properly
- API rate limiting respect
- Secure credential storage
- Input validation and sanitization
- SQL injection prevention (parameterized queries)

### Maintainability
- Clear code documentation
- Modular design
- Unit tests for critical components
- Configuration-driven behavior
- Version control best practices
- Change log maintenance

---

## 11. USAGE EXAMPLES

### CLI Examples

```bash
# Fetch latest data
python -m src.scripts.fetch_data --all

# Calculate indicators for all stocks
python -m src.scripts.calculate_indicators --all

# Screen for golden cross signals
python -m src.api.cli screen --signal golden_cross --min-strength 60

# Get top opportunities today
python -m src.api.cli top --limit 20

# Screen by sector
python -m src.api.cli screen --sector "Banking" --signal rsi_oversold

# Custom screening
python -m src.api.cli screen --custom "rsi<30 and volume_breakout and macd_bullish"

# Backtest a signal
python -m src.api.cli backtest --signal golden_cross --period 365

# Export results
python -m src.api.cli screen --signal all --export csv --output results.csv
```

### API Examples (if REST API implemented)

```bash
# Get stock list
GET /api/stocks

# Get signals for a stock
GET /api/signals/BBCA

# Screen stocks
POST /api/screen
{
  "signal_type": "golden_cross",
  "min_strength": 60,
  "sector": "Banking"
}

# Get top opportunities
GET /api/opportunities?limit=20
```

---

## 12. CONFIGURATION

### settings.yaml Example

```yaml
database:
  path: "./database/stockCode.sqlite"
  backup_enabled: true
  backup_path: "./database/backups/"

data_sources:
  stock_list_url: "https://139.255.96.106:1443/GetAllStock"
  price_data_url: "https://idxmobile.co.id//Data/hsx"
  verify_ssl: false
  timeout: 30
  retry_attempts: 3

indicators:
  sma_periods: [20, 50, 200]
  ema_periods: [12, 26]
  rsi_period: 14
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9
  bollinger_period: 20
  bollinger_std: 2
  atr_period: 14

signals:
  min_strength: 50
  volume_breakout_threshold: 2.0
  rsi_oversold: 30
  rsi_overbought: 70

scheduling:
  data_fetch_time: "16:00"  # After market close
  indicator_calc_time: "16:30"
  signal_detect_time: "17:00"

logging:
  level: "INFO"
  file: "./logs/screener.log"
  max_size: "10MB"
  backup_count: 5
```

---

## 13. NEXT STEPS

### Immediate Actions
1. Set up development environment
2. Initialize project structure
3. Create database schema
4. Implement basic data fetcher
5. Test data ingestion with sample stocks

### Questions to Address
- What is the market schedule? (trading hours, holidays)
- Are there rate limits on the data APIs?
- What is the typical response format from the APIs?
- Do you want real-time updates or end-of-day only?
- What is your preferred deployment environment?

### Success Metrics
- Data freshness: < 1 hour after market close
- Calculation time: < 5 minutes for all stocks
- Signal accuracy: > 60% win rate (to be validated)
- System uptime: > 99%
- Query response time: < 2 seconds

---

## 14. RESOURCES & REFERENCES

### Technical Analysis Libraries
- TA-Lib: https://github.com/mrjbq7/ta-lib
- pandas-ta: https://github.com/twopirllc/pandas-ta
- finta: https://github.com/peerchemist/finta

### Documentation
- Technical Analysis: https://www.investopedia.com/technical-analysis-4689657
- SQLite: https://www.sqlite.org/docs.html
- Pandas: https://pandas.pydata.org/docs/

### Best Practices
- Database design for time series: https://www.timescale.com/blog/time-series-data/
- Python project structure: https://docs.python-guide.org/writing/structure/
- Financial data handling: ISO 20022 standards

---

*Document Version: 1.0*
*Last Updated: 2025-10-31*
*Author: Claude Code*
