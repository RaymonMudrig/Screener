# Quick Start Guide

## Installation

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

**Note**: Some dependencies may require additional system libraries:

- **TA-Lib**: Requires TA-Lib C library
  - macOS: `brew install ta-lib`
  - Linux: See https://github.com/mrjbq7/ta-lib#dependencies
  - Windows: Download from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

If you encounter issues with TA-Lib, you can use `pandas-ta` only for Phase 1.

### 2. Initialize Database

```bash
python3 -m src.api.cli init
```

This creates the SQLite database at `database/stockCode.sqlite` with all required tables and indexes.

### 3. Fetch Stock List

```bash
python3 -m src.api.cli update-stocks
```

This fetches the latest list of stocks from IDX and populates the `stocks` table.

### 4. Fetch Price Data

For a single stock (example: BBCA):
```bash
python3 -m src.api.cli update-price BBCA --days 365
```

For multiple stocks (test with limit):
```bash
python3 -m src.api.cli update-all --limit 5 --delay 2.0
```

### 5. View Data

List stocks:
```bash
python3 -m src.api.cli list-stocks --limit 20
```

Show price data:
```bash
python3 -m src.api.cli show-price BBCA --limit 10
```

Check database stats:
```bash
python3 -m src.api.cli stats
```

## Quick Setup Script

Run the automated setup script:
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## Common Issues

### SSL Certificate Error
If you see SSL certificate errors when fetching stock list, this is expected. The IDX API uses a self-signed certificate. SSL verification is disabled in the configuration.

### Module Not Found
Make sure you're running commands from the project root directory (`/Users/raymonmudrig/AI/Screener`).

### Rate Limiting
If you're updating all stocks, use the `--delay` parameter (recommended: 1-2 seconds) to avoid overwhelming the API server.

### Database Locked
If you see "database is locked" errors, make sure no other process is accessing the database.

## What's Next?

After Phase 1 setup is complete, the next steps are:

1. **Calculate Technical Indicators** (Phase 2)
   - Implement indicator calculation modules
   - Pre-calculate indicators for all stocks

2. **Implement Signal Detection** (Phase 2)
   - Create signal detector modules
   - Detect trading signals based on indicators

3. **Build Screening Engine** (Phase 2)
   - Screen stocks by signals
   - Create pre-built strategies

## Directory Structure

```
stock-screener/
├── src/              # Source code
├── database/         # SQLite database
├── config/           # Configuration files
├── logs/             # Application logs
├── scripts/          # Utility scripts
└── tests/            # Tests
```

## CLI Command Reference

| Command | Description |
|---------|-------------|
| `init` | Initialize database |
| `stats` | Show database statistics |
| `update-stocks` | Fetch stock list from IDX |
| `update-price <stock>` | Update price data for a stock |
| `update-all` | Update all stocks |
| `list-stocks` | List all stocks |
| `show-price <stock>` | Show price data |
| `info <stock>` | Show stock information |
| `quality <stock>` | Generate quality report |

## Support

For detailed documentation, see:
- `README.md` - Full documentation
- `.claude/TECHNICAL_SIGNAL_PLAN.md` - System architecture and plan
- `config/settings.yaml` - Configuration options
