# Stock Screener - Quick Reference Guide

## 🚀 Complete System Workflow

### 1️⃣ Initial Setup

```bash
# Install dependencies
pip3 install -r requirements.txt

# Initialize database
python3 -m src.api.cli init
```

### 2️⃣ Fetch Stock Data

```bash
# Fetch stock list from IDX
python3 -m src.api.cli update-stocks

# Update single stock (365 days)
python3 -m src.api.cli update-price BBCA

# Update all stocks (batch)
python3 scripts/batch_update.py --delay 1.5
```

### 3️⃣ Calculate Indicators

```bash
# Single stock
python3 -m src.api.cli calculate-indicators BBCA

# All stocks
python3 -m src.api.cli calculate-all-indicators
```

### 4️⃣ Detect Signals

```bash
# Single stock
python3 -m src.api.cli detect-signals BBCA

# All stocks
python3 -m src.api.cli detect-all-signals
```

### 5️⃣ View Opportunities

```bash
# Top 20 opportunities
python3 -m src.api.cli top-opportunities --limit 20

# View all signals
python3 -m src.api.cli show-signals

# Filter by type
python3 -m src.api.cli show-signals --signal-type trend --min-strength 70
```

---

## 📋 All CLI Commands

### Database & Setup
```bash
init                            # Initialize database
stats                           # Show database statistics
```

### Stock Data
```bash
update-stocks                   # Fetch stock list from IDX
update-price STOCK              # Update single stock price data
update-all                      # Update all stocks
list-stocks                     # List all stocks
show-price STOCK                # Show price data for stock
info STOCK                      # Show stock information
quality STOCK                   # Data quality report
```

### Technical Indicators
```bash
calculate-indicators STOCK      # Calculate indicators for stock
calculate-all-indicators        # Calculate for all stocks
show-indicators STOCK           # Show latest indicators
```

### Signal Detection
```bash
detect-signals STOCK            # Detect signals for stock
detect-all-signals              # Detect for all stocks
show-signals                    # Show all active signals
top-opportunities               # Top opportunities by strength
```

### Intraday Refresh
```bash
refresh-intraday                # Refresh prices, indicators & signals (all-in-one)
refresh-intraday --delay 1.0    # With custom delay
refresh-intraday --skip-price-update  # Only recalculate indicators/signals
```

---

## 🎯 Common Use Cases

### Intraday Monitoring (RECOMMENDED)

**All-in-one refresh command:**
```bash
# Fetch latest prices, recalculate indicators, detect signals
python3 -m src.api.cli refresh-intraday --delay 1.0
```

**Automated scheduling:**
```bash
# Option 1: Python scheduler (runs every 15 min during trading hours)
python3 scripts/scheduler_intraday.py

# Option 2: Cron job (edit with: crontab -e)
*/15 9-16 * * 1-5 cd /path/to/Screener && python3 -m src.api.cli refresh-intraday
```

See `INTRADAY_REFRESH.md` for complete automation guide.

### Daily Screening Workflow (LEGACY)

```bash
# 1. Update latest price data (incremental)
python3 scripts/batch_update.py --skip-stock-list --delay 1.0

# 2. Calculate new indicators
python3 -m src.api.cli calculate-all-indicators

# 3. Detect new signals
python3 -m src.api.cli detect-all-signals

# 4. View top opportunities
python3 -m src.api.cli top-opportunities --limit 20
```

**Note:** The new `refresh-intraday` command does all 4 steps automatically!

### Analyze Specific Stock

```bash
# Complete analysis
python3 -m src.api.cli show-price BBCA --limit 10
python3 -m src.api.cli show-indicators BBCA
python3 -m src.api.cli detect-signals BBCA
```

### Find Specific Signals

```bash
# Trend signals only
python3 -m src.api.cli show-signals --signal-type trend

# Strong momentum signals
python3 -m src.api.cli show-signals --signal-type momentum --min-strength 70

# High strength signals
python3 -m src.api.cli show-signals --min-strength 80
```

---

## 📊 Signal Types Reference

### Trend Signals (Long-term)
- **Golden Cross** (60-100): SMA50 > SMA200 ↑ Strong bullish
- **Death Cross** (60-100): SMA50 < SMA200 ↓ Strong bearish
- **Fast Cross** (50-85): SMA20 crosses SMA50 (earlier signals)
- **MACD Crossover** (55-90): MACD crosses signal line
- **MACD Histogram** (45-75): Momentum reversal

### Momentum Signals (Short-term)
- **RSI Oversold** (45-85): RSI < 30 ↑ Reversal up
- **RSI Overbought** (45-85): RSI > 70 ↓ Reversal down
- **RSI Midline** (50-80): RSI crosses 50
- **Stochastic** (60-90): %K crosses %D in extremes
- **Divergence** (60-90): Price/indicator mismatch

### Volatility Signals
- **BB Squeeze** (55): Low volatility → breakout pending
- **BB Breakout** (60-95): Price breaks bands
- **Walking Bands** (50): Strong trend continuation
- **ATR Expansion** (45): Increased volatility

### Volume Signals
- **Volume Breakout** (65-100): Volume > 2x average
- **OBV Divergence** (60-90): Volume/price mismatch
- **CMF** (55): Strong buying/selling pressure
- **MFI** (50): Volume-weighted RSI extremes

---

## ⚙️ Configuration

Edit `config/settings.yaml`:

```yaml
# Data fetching
fetching:
  fetch_history_days: 365       # Default history to fetch

# Indicators
indicators:
  sma_periods: [20, 50, 200]
  rsi_period: 14
  bollinger_period: 20

# Signals
signals:
  min_strength: 50              # Default minimum strength
  volume_breakout_threshold: 2.0  # 2x average
  rsi_oversold: 30
  rsi_overbought: 70
  signal_expiry_days: 5         # Auto-deactivate old signals

# Logging
logging:
  level: "INFO"                 # DEBUG, INFO, WARNING, ERROR
```

---

## 🔍 Screening Strategies

### Conservative (Low Risk)
```bash
# Look for strong trend signals with confirmation
python3 -m src.api.cli show-signals --signal-type trend --min-strength 75
```

Focus on:
- Golden Cross with volume
- MACD crossover above zero
- RSI > 50 in uptrend

### Aggressive (High Risk/Reward)
```bash
# Look for early momentum signals
python3 -m src.api.cli show-signals --signal-type momentum --min-strength 65
```

Focus on:
- Fast Cross (SMA20/50)
- RSI extremes with bounce
- Stochastic in oversold
- Volume breakouts

### Balanced (Medium Risk)
```bash
# Look for multiple confirming signals
python3 -m src.api.cli top-opportunities --limit 30
```

Focus on:
- Multiple signal types aligning
- Volume confirmation
- Trend alignment
- Strength > 70

---

## 📈 System Status Levels

### ✅ Fully Operational
- Price data: 365 days for all stocks
- Indicators: 40+ calculated
- Signals: 25+ types detected
- Database: Optimized with indexes

### To Check Health:
```bash
python3 -m src.api.cli stats
```

Expected output:
- Active stocks: 500-800
- Price records: 150,000-300,000
- Indicator records: 5M-15M
- Active signals: 100-1000

---

## 🛠️ Troubleshooting

### "Insufficient data" error
```bash
# Re-fetch with full history
python3 -m src.api.cli update-price STOCK
```

### "No indicators found"
```bash
# Calculate indicators first
python3 -m src.api.cli calculate-indicators STOCK
```

### "No signals detected"
This is normal! Not all stocks have signals at all times.
- Try lowering `--min-strength`
- Check if indicators are calculated
- Verify price data is recent

### Database locked
Close other processes accessing the database.

---

## 📁 Project Structure

```
stock-screener/
├── src/
│   ├── data/          # Data fetching & validation
│   ├── indicators/    # Technical indicators (40+)
│   ├── signals/       # Signal detection (25+)
│   ├── api/           # CLI interface
│   └── utils/         # Config, logging, database
├── database/          # SQLite database
├── config/            # Configuration files
├── logs/              # Application logs
└── scripts/           # Utility scripts
```

---

## 🎓 Learning Resources

**Indicator Documentation**:
- `PHASE2_COMPLETE.md` - All indicators explained
- `TECHNICAL_SIGNAL.md` - Original signal specifications
- `TECHNICAL_SIGNAL_PLAN.md` - System architecture

**Signal Documentation**:
- `PHASE3_COMPLETE.md` - All signals explained
- Config: `config/settings.yaml`

---

## 💡 Tips

1. **Run daily updates incrementally** - Much faster than full updates
2. **Start with high-strength signals** (>70) to reduce noise
3. **Combine multiple signal types** for better accuracy
4. **Use trend signals for direction**, momentum for timing
5. **Volume confirmation** adds significant reliability
6. **Check signal date** - Recent signals are more actionable

---

**Version**: 1.0.0
**Last Updated**: 2025-10-31
**Status**: Phases 1-3 Complete ✅
