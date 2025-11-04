# IDX Stock Screener - Documentation Index

## Documentation Files

This directory contains comprehensive documentation for understanding and implementing the custom user pattern feature for the IDX Stock Screener.

### 1. **CODEBASE_SUMMARY.md** (21 KB)
Complete technical reference for the entire codebase.

**Contents:**
- Project overview and architecture
- Pattern system architecture (10 preset patterns)
- Technical signals (Trend, Momentum, Volatility, Volume)
- Fundamental metrics (Valuation, Profitability, Growth, Health, Quality)
- Pattern execution and screening logic
- Frontend architecture and components
- Project structure and file organization
- Database schema reference
- Configuration areas
- API endpoints reference
- Implementation notes

**Best for:** Understanding the complete system, technical details, and how components interact

### 2. **CUSTOM_PATTERN_GUIDE.md** (12 KB)
Implementation guide for creating custom user patterns.

**Contents:**
- Pattern definition structure and JSON format
- All available technical signals with descriptions
- All available fundamental metrics with ranges
- Pattern categories and examples
- Implementation options (Python, API, CLI)
- Pattern validation rules
- Pattern execution and scoring explanation
- Testing procedures
- Common pattern templates
- Troubleshooting guide
- File location references

**Best for:** Creating custom patterns, understanding available signals/metrics, implementation examples

### 3. **README.md** (6 KB)
Original project README with setup and usage instructions.

---

## Quick Reference

### Where to Find Information

**Want to understand the pattern system?**
- Read: CODEBASE_SUMMARY.md, Section 1 & 4
- Files: `/src/patterns/engine.py`, `/src/patterns/storage.py`

**Want to see available technical signals?**
- Read: CUSTOM_PATTERN_GUIDE.md, Section 2
- OR: CODEBASE_SUMMARY.md, Section 2
- Files: `/src/signals/trend_signals.py`, `/src/signals/momentum_signals.py`, etc.

**Want to see available fundamental metrics?**
- Read: CUSTOM_PATTERN_GUIDE.md, Section 3
- OR: CODEBASE_SUMMARY.md, Section 3
- Files: `/src/fundamentals/ratios.py`, `/src/fundamentals/screener.py`

**Want to create a custom pattern?**
- Read: CUSTOM_PATTERN_GUIDE.md, Sections 1-5
- Examples: CUSTOM_PATTERN_GUIDE.md, Section 5
- Testing: CUSTOM_PATTERN_GUIDE.md, Section 9

**Want to understand the frontend?**
- Read: CODEBASE_SUMMARY.md, Section 5
- Files: `/web/app.js`, `/web/index.html`

**Want to understand the API?**
- Read: CODEBASE_SUMMARY.md, Section 9
- Files: `/src/api/web.py`

**Want to understand the database schema?**
- Read: CODEBASE_SUMMARY.md, Section 7
- Files: `/scripts/create_pattern_tables.py`

**Need to troubleshoot?**
- Read: CUSTOM_PATTERN_GUIDE.md, Section 11

---

## Key Concepts

### Pattern
A screening strategy that combines technical signals and/or fundamental metrics to find matching stocks.

**Structure:**
- Pattern ID (unique identifier)
- Pattern Name (display name)
- Category (value/growth/quality/health/technical/custom)
- Technical Criteria (signals required + strength threshold)
- Fundamental Criteria (metric ranges)
- Sort By (which field to sort results by)

### Technical Signal
A price/volume-based indicator that detects trading opportunities.

**Types:**
- TREND: Moving averages, MACD, crossovers
- MOMENTUM: RSI, Stochastic, CCI, Williams %R
- VOLATILITY: Bollinger Bands, ATR
- VOLUME: Volume breakouts

**Properties:**
- Signal Name (unique identifier)
- Type (TREND, MOMENTUM, etc.)
- Direction (BULLISH, BEARISH, NEUTRAL)
- Strength (0-100 scale)
- Date (when detected)

### Fundamental Metric
A financial ratio or measurement from company financial statements.

**Categories:**
- Valuation: P/E, P/B, P/S, PEG, EV/EBITDA
- Profitability: ROE, ROA, ROIC, Net Profit Margin
- Growth: Revenue Growth, EPS Growth
- Financial Health: Current Ratio, Debt/Assets, Quick Ratio
- Quality: Piotroski Score, Altman Z-Score

### Screening
The process of executing a pattern against the stock database to find matching stocks.

**Steps:**
1. Load pattern definition
2. Screen fundamental criteria (get matching stocks)
3. Screen technical criteria (get stocks with signals)
4. Combine results
5. Score results (0-100)
6. Sort and cache

### Match Score
A numerical rating (0-100) of how well a stock matches a pattern.

**Calculation:**
- Pure technical: Average signal strength
- Pure fundamental: Percentage of met criteria
- Combined: 60% fundamental + 40% technical

---

## Architecture Overview

```
Frontend (Browser)
    |
    | HTTP REST API
    |
Backend (Flask)
    |
    +-- Pattern Engine (execute patterns)
    |       |
    |       +-- Fundamental Screener (query metrics)
    |       |
    |       +-- Signal Database (query signals)
    |       |
    |       +-- Scoring Engine (calculate scores)
    |
    +-- Signal Engine (detect technical signals)
    |       |
    |       +-- Trend Detector
    |       +-- Momentum Detector
    |       +-- Volatility Detector
    |       +-- Volume Detector
    |
    +-- Data Management
            |
            +-- SQLite Database
                    |
                    +-- Patterns
                    +-- Pattern Results Cache
                    +-- Signals
                    +-- Indicators
                    +-- Fundamental Data
                    +-- Price Data
                    +-- Stock Info
```

---

## Implementation Workflow

### To Create a Custom Pattern:

1. **Define the pattern** (JSON structure)
   - Pattern ID, Name, Category
   - Technical criteria (optional)
   - Fundamental criteria (optional)

2. **Choose implementation method**
   - Python API: `PatternStorage.create_pattern()`
   - HTTP API: POST `/api/patterns`
   - CLI: (if implemented)

3. **Test the pattern**
   - Execute with `PatternEngine.run_pattern()`
   - Verify results in frontend
   - Check scores and signals

4. **Refine if needed**
   - Adjust criteria ranges
   - Change signals
   - Update sort field
   - Delete and recreate pattern

### To Modify the Screening Logic:

1. **Understand current flow** (CODEBASE_SUMMARY.md, Section 4)

2. **Identify where changes needed**
   - PatternEngine: pattern execution flow
   - FundamentalScreener: fundamental metric screening
   - Signal detection: technical signal matching
   - Scoring: how results are scored

3. **Implement changes**
   - Follow existing code patterns
   - Maintain JSON compatibility
   - Update tests

4. **Verify changes**
   - Test with existing patterns
   - Create test patterns
   - Check database consistency

---

## File Structure Reference

```
DOCUMENTATION:
- CODEBASE_SUMMARY.md          (this directory)
- CUSTOM_PATTERN_GUIDE.md      (this directory)
- DOCUMENTATION_INDEX.md       (this directory)
- README.md                    (original project readme)

PATTERN SYSTEM:
- src/patterns/engine.py       (Pattern execution)
- src/patterns/storage.py      (Pattern CRUD)
- scripts/create_pattern_tables.py (DB setup)

TECHNICAL SIGNALS:
- src/signals/engine.py        (Signal orchestration)
- src/signals/detector.py      (Base signal class)
- src/signals/trend_signals.py
- src/signals/momentum_signals.py
- src/signals/volatility_signals.py
- src/signals/volume_signals.py

FUNDAMENTAL ANALYSIS:
- src/fundamentals/screener.py (Main screening logic)
- src/fundamentals/ratios.py   (Ratio calculations)
- src/fundamentals/growth.py   (Growth metrics)
- src/fundamentals/quality.py  (Quality scores)
- src/fundamentals/ttm.py      (TTM calculations)
- src/fundamentals/storage.py  (Data storage)
- src/fundamentals/fetcher.py  (Data fetching)

FRONTEND:
- web/index.html               (HTML structure)
- web/app.js                   (All frontend logic)
- web/style.css                (Styling)

API:
- src/api/web.py               (Flask endpoints)
- src/api/cli.py               (CLI interface)

DATABASE:
- database/stockCode.sqlite    (SQLite database)
```

---

## Common Tasks

### Add a new technical signal type
1. Create detector class in `/src/signals/`
2. Register in `SignalEngine.__init__()` 
3. Add signal name to CUSTOM_PATTERN_GUIDE.md Section 2
4. Document in CODEBASE_SUMMARY.md Section 2

### Add a new fundamental metric
1. Add calculation to `/src/fundamentals/ratios.py`
2. Add screening method to `/src/fundamentals/screener.py`
3. Add to CUSTOM_PATTERN_GUIDE.md Section 3
4. Document in CODEBASE_SUMMARY.md Section 3

### Add a new pattern category
1. Add to pattern categories list in database
2. Update frontend grouping in `/web/app.js`
3. Document in CUSTOM_PATTERN_GUIDE.md Section 4

### Change scoring algorithm
1. Modify `PatternEngine._score_results()` in `/src/patterns/engine.py`
2. Update documentation in CODEBASE_SUMMARY.md Section 4
3. Test with existing patterns

### Change result caching
1. Modify `PatternStorage` cache methods
2. Update TTL in `PatternEngine.run_pattern()`
3. Document changes in CODEBASE_SUMMARY.md Section 4

---

## Development Notes

### Database
- SQLite3 at `database/stockCode.sqlite`
- Primary tables: `screening_patterns`, `pattern_results_cache`, `signals`, `fundamental_data`
- Indexes on: category, preset flag, match_score, last_updated
- Foreign keys: pattern_id (cascade delete), stock_id

### API
- Flask application running on default port
- CORS enabled for all routes
- JSON request/response format
- No authentication implemented

### Frontend
- Vanilla JavaScript (no frameworks)
- Fetch API for HTTP calls
- Local state management with global variables
- Event listeners for user interactions
- Formatting helpers for display (signals, metrics, numbers)

### Performance
- Pattern results cached for 24 hours
- Cache can be cleared manually
- Queries optimized with indexes
- Signal queries filtered by date (last 7 days) and status (active only)

---

## Support & Troubleshooting

### Common Issues

**Pattern returns no results**
- Check min/max ranges are reasonable
- Verify stocks have required metrics (for fundamental)
- Check signals exist in database (for technical)

**Pattern validation fails**
- Ensure pattern_id is unique
- Check required fields: pattern_id, pattern_name, category
- Verify signal names match exactly (case-sensitive, lowercase)

**API returns 404**
- Verify pattern_id exists
- Check endpoint spelling

**Frontend dropdown empty**
- Check database connection
- Verify patterns table has data

**Scoring seems wrong**
- Review scoring calculation in CODEBASE_SUMMARY.md Section 4
- Check pattern weightings (60% fundamental, 40% technical)
- Verify individual criteria met/not met

---

## References

### Internal Documentation
- CODEBASE_SUMMARY.md - Full technical reference
- CUSTOM_PATTERN_GUIDE.md - Implementation guide
- Code comments in source files

### External Resources
- SQLite: https://www.sqlite.org/
- Flask: https://flask.palletsprojects.com/
- Financial Ratios: Investment finance references
- Technical Analysis: Trading literature references

---

**Last Updated:** November 3, 2025
**Documentation Version:** 1.0
**Project Version:** First working version (d3c4a86)
