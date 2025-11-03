# Technical Signals Classification for Price Data Analysis

I want to build Stock Screener based on price data.
Data stored to sqlite file stockCode.sqlite to preserve data.

## Data Source:

### Stock List

```
https://139.255.96.106:1443/GetAllStock
```

### Price Data
```
https://idxmobile.co.id//Data/hsx?stockID={stockID}&code={startDate}-{endDate}
```
- stockID: valid value listed from stock list above.
- Date format: m/d/yyyy

example:
https://idxmobile.co.id//Data/hsx?stockID=BBCA&code=6/18/2024-7/10/2025

---

Let me provide you with a comprehensive taxonomy of technical signals that can be built from price data.

## 1. **TREND-FOLLOWING SIGNALS**

### Moving Average Based
- **Golden Cross / Death Cross** (50/200 MA)
- **Fast Cross** (20/50 MA) - Earlier signals
- **Triple Moving Average** - 3 MA alignment
- **MA Envelope Breakouts** - Price breaks MA bands
- **MA Slope Changes** - Detecting trend acceleration/deceleration
- **Displaced Moving Averages** - Forward/backward shifted MAs
- **MACD Crossovers** - MACD line crosses signal line
- **MACD Histogram Reversals** - Momentum shifts
- **MACD Divergence** - Price vs MACD direction mismatch

### Trend Channel & Line Based
- **Trendline Breaks** - Support/resistance violations
- **Channel Breakouts** - Price escapes parallel channels
- **Donchian Channel** - Highest high/lowest low breakouts
- **Keltner Channel** - ATR-based channel breaks
- **Parabolic SAR Flips** - Stop and reverse signals

### Directional Movement
- **ADX Crossovers** - Trend strength threshold breaks
- **+DI/-DI Crossovers** - Directional indicator crosses
- **Aroon Crossovers** - Aroon up/down intersections
- **Supertrend Flips** - ATR-based trend changes

---

## 2. **MOMENTUM & OSCILLATOR SIGNALS**

### Overbought/Oversold
- **RSI Extremes** - Above 70 (overbought) / Below 30 (oversold)
- **RSI Midline Cross** - Crossing 50 level
- **Stochastic Extremes** - %K in overbought/oversold zones
- **Stochastic Crossovers** - %K crosses %D
- **Williams %R Signals** - Extreme readings
- **CCI Threshold Breaks** - +100/-100 crosses
- **Money Flow Index** - Volume-weighted RSI signals

### Momentum Changes
- **Rate of Change (ROC)** - Acceleration crosses zero
- **Momentum Indicator** - Zero line crossovers
- **TSI (True Strength Index)** - Double-smoothed momentum
- **Ultimate Oscillator** - Multi-timeframe momentum
- **Awesome Oscillator** - Histogram color changes

### Divergences
- **Bullish Divergence** - Price lower low, indicator higher low
- **Bearish Divergence** - Price higher high, indicator lower high
- **Hidden Divergences** - Trend continuation signals
- **Triple Divergence** - Stronger divergence confirmation

---

## 3. **VOLATILITY SIGNALS**

### Bollinger Bands
- **Band Squeeze** - Low volatility (bands narrow)
- **Band Expansion** - Volatility breakout
- **Walking the Bands** - Strong trend riding upper/lower band
- **Double Bollinger Bands** - Multiple standard deviations
- **Bollinger Band Width** - Volatility measurement
- **%B Indicator** - Position within bands

### Volatility Breakouts
- **ATR Expansion** - Volatility increasing
- **ATR Contraction** - Calm before storm
- **Historical Volatility Breaks** - Unusual volatility levels
- **Narrow Range Days** - Compression patterns
- **Wide Range Days** - Expansion signals

### Price Action Volatility
- **Inside Bars** - Consolidation patterns
- **Outside Bars** - Volatility expansion
- **Volatility Ratio** - Current vs historical volatility

---

## 4. **VOLUME-BASED SIGNALS**

### Volume Confirmation
- **Volume Breakout** - Above average volume
- **Climax Volume** - Extremely high volume (exhaustion)
- **Diminishing Volume** - Trend weakness
- **Volume Price Trend (VPT)** - Cumulative volume direction
- **Price-Volume Trend** - Volume-weighted price changes

### Volume Oscillators
- **OBV (On Balance Volume)** - Divergences and breakouts
- **Chaikin Money Flow** - Buying/selling pressure
- **Money Flow Index** - Volume-weighted RSI
- **Accumulation/Distribution** - Institutional activity
- **Volume Oscillator** - Fast/slow volume MA cross
- **Klinger Oscillator** - Volume force indicator

### Volume Patterns
- **Volume Spike** - Sudden interest
- **Drying Volume** - Consolidation phase
- **Volume at Price** - Volume profile analysis
- **VWAP Crosses** - Volume weighted average price

---

## 5. **PRICE PATTERN SIGNALS**

### Candlestick Patterns
- **Engulfing Patterns** - Bullish/bearish reversals
- **Doji Patterns** - Indecision signals
- **Hammer/Shooting Star** - Reversal candles
- **Morning/Evening Star** - Three-candle reversals
- **Three White Soldiers/Black Crows** - Strong trends
- **Harami Patterns** - Inside day reversals
- **Marubozu** - Strong directional candles

### Chart Patterns
- **Head and Shoulders** - Reversal pattern completion
- **Double Top/Bottom** - Support/resistance tests
- **Triangle Breakouts** - Ascending, descending, symmetrical
- **Wedge Patterns** - Rising/falling wedge breaks
- **Flag/Pennant** - Continuation patterns
- **Cup and Handle** - Bullish continuation
- **Rounding Bottom/Top** - Gradual reversals

### Price Levels
- **Support/Resistance Breaks** - Key level violations
- **Fibonacci Retracements** - Key level touches
- **Pivot Point Breaks** - Daily/weekly pivots
- **Round Number Psychology** - Whole number breaks
- **52-Week High/Low** - Breakout signals

---

## 6. **GAP SIGNALS**

- **Gap Up/Down** - Opening price jumps
- **Gap Fill** - Price returns to close gap
- **Breakaway Gap** - Trend start confirmation
- **Continuation Gap** - Mid-trend momentum
- **Exhaustion Gap** - Trend ending signal
- **Island Reversal** - Gaps on both sides

---

## 7. **MULTI-TIMEFRAME SIGNALS**

- **Higher Timeframe Alignment** - Trend confirmation across periods
- **Fractal Breakouts** - Williams Fractals
- **Timeframe Divergence** - Conflicting signals
- **Ichimoku Cloud** - Multiple component signals
  - Tenkan/Kijun Cross
  - Cloud Breaks
  - Chikou Span confirmation
  - Cloud color changes

---

## 8. **STATISTICAL SIGNALS**

### Mean Reversion
- **Z-Score Extremes** - Standard deviation from mean
- **Bollinger %B Extremes** - Distance from bands
- **Mean Reversion Bands** - Custom statistical bands
- **Regression Channel** - Linear regression breaks

### Correlation & Relative Strength
- **Relative Strength** - Stock vs Index/Sector
- **Correlation Breaks** - Normal correlation disruption
- **Beta Deviation** - Unusual relative movement
- **Inter-market Signals** - Cross-asset correlation

---

## 9. **HYBRID/COMPOSITE SIGNALS**

### Custom Combinations
- **Elder's Triple Screen** - Multiple timeframe + oscillator
- **Market Thrust** - Volume + breadth + momentum
- **Zweig Breadth Thrust** - Market momentum signal
- **Price Rate of Change + Volume** - Combined strength
- **Trend + Volatility + Volume** - Multi-factor confirmation

### Scoring Systems
- **Technical Score Card** - Multiple indicator weighted score
- **Signal Strength Index** - Aggregate signal power
- **Confirmation Count** - Number of aligned indicators

---

## 10. **ADVANCED SIGNALS**

### Market Microstructure
- **Bid-Ask Spread Changes** - Liquidity signals
- **Order Flow Imbalance** - Buying/selling pressure
- **Time and Sales Patterns** - Trade size analysis

### Machine Learning Enhanced
- **Anomaly Detection** - Unusual pattern identification
- **Pattern Recognition** - ML-identified formations
- **Predictive Signals** - Probability-based forecasts
- **Sentiment Integration** - Price + alternative data

---

## **SIGNAL QUALITY FACTORS**

When building any signal, consider enhancing with:

1. **Confirmation Filters**
   - Volume confirmation
   - Multiple timeframe agreement
   - Sector/market alignment
   - Volatility context

2. **Strength Metrics**
   - Distance from threshold
   - Speed of signal development
   - Historical reliability
   - Current market regime

3. **Risk Assessment**
   - Signal failure rate
   - Average drawdown
   - Win/loss ratio
   - Risk-adjusted returns

4. **Timing Factors**
   - Signal age
   - Time of day (intraday)
   - Day of week
   - Market session

---

## **RECOMMENDED SIGNAL COMBINATIONS**

For a robust screener, consider combining:

**Conservative Approach:**
- Golden Cross + Volume confirmation + RSI > 50
- Trend + Momentum + Volume alignment

**Aggressive Approach:**
- Fast MA cross + Volatility breakout + Volume spike
- Multiple oscillator extremes + Divergence

**Balanced Approach:**
- Price pattern + MA trend + Volume + Momentum oscillator