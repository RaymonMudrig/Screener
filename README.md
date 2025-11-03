# Stock Screener - Indonesian Stock Exchange

A comprehensive technical analysis stock screener for the Indonesian Stock Exchange (IDX), built with Python and SQLite.

## Features

- **Data Collection**: Automatically fetch stock lists and historical price data from IDX
- **Data Validation**: Validate and clean price data with quality reporting
- **Technical Indicators**: Calculate 20+ technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, etc.)
- **Signal Detection**: Detect trading signals (Golden Cross, RSI extremes, MACD crossovers, etc.)
- **Screening Engine**: Filter stocks based on signals and custom criteria
- **CLI Interface**: Command-line interface for easy data management
- **SQLite Database**: Efficient local storage with optimized indexes

## Project Structure

```
stock-screener/
├── src/
│   ├── data/           # Data fetching, validation, storage
│   ├── indicators/     # Technical indicator calculations
│   ├── signals/        # Signal detection logic
│   ├── screener/       # Screening engine
│   ├── api/            # CLI and API interfaces
│   └── utils/          # Configuration, logging, database
├── database/           # SQLite database storage
├── config/             # Configuration files
├── logs/               # Application logs
├── scripts/            # Utility scripts
└── tests/              # Unit tests
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. Clone the repository or navigate to the project directory:
```bash
cd /Users/raymonmudrig/AI/Screener
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python -m src.api.cli init
```

## Usage

### CLI Commands

#### Initialize Database
```bash
python -m src.api.cli init
```

#### Update Stock List
Fetch the latest list of stocks from IDX:
```bash
python -m src.api.cli update-stocks
```

#### Update Price Data for a Specific Stock
```bash
python -m src.api.cli update-price BBCA --days 365
```

#### Update All Stocks
Fetch price data for all stocks (with rate limiting):
```bash
python -m src.api.cli update-all --limit 10 --delay 1.0
```

#### View Database Statistics
```bash
python -m src.api.cli stats
```

#### List All Stocks
```bash
python -m src.api.cli list-stocks --limit 20
```

#### Show Price Data
```bash
python -m src.api.cli show-price BBCA --limit 10
```

#### View Stock Information
```bash
python -m src.api.cli info BBCA
```

#### Data Quality Report
```bash
python -m src.api.cli quality BBCA
```

### Python API

```python
from src.data.storage import DataStorage

# Initialize storage
storage = DataStorage()

# Update stock list
count = storage.update_stock_list()

# Update price data for a stock
records = storage.update_price_data('BBCA')

# Get price data
price_data = storage.get_price_data('BBCA')

# Get database statistics
stats = storage.get_stats()

# Generate quality report
report = storage.generate_quality_report('BBCA')
```

## Configuration

Edit `config/settings.yaml` to customize:

- Database path
- Data source URLs
- Technical indicator parameters
- Signal detection thresholds
- Logging settings
- Performance options

## Data Sources

### Stock List
- URL: `https://139.255.96.106:1443/GetAllStock`
- Contains: Stock codes, names, sectors, subsectors

### Price Data
- URL: `https://idxmobile.co.id//Data/hsx`
- Format: `?stockID={stockID}&code={startDate}-{endDate}`
- Date Format: `m/d/yyyy`
- Example: `https://idxmobile.co.id//Data/hsx?stockID=BBCA&code=6/18/2024-7/10/2025`

## Development Roadmap

### Phase 1: Foundation ✓ (Completed)
- [x] Database setup and schema
- [x] Data ingestion pipeline
- [x] Basic price data storage
- [x] Core technical indicators
- [x] CLI interface

### Phase 2: Signal Detection (Next)
- [ ] Implement signal detectors
- [ ] Signal strength scoring
- [ ] Basic screening functionality
- [ ] Automated updates

### Phase 3: Advanced Features
- [ ] Additional indicators (30+ total)
- [ ] Multi-timeframe analysis
- [ ] Pattern recognition
- [ ] Backtesting framework

### Phase 4: Enhancement
- [ ] Web dashboard
- [ ] Alert system
- [ ] API documentation
- [ ] Performance optimization

## Technical Indicators (Planned)

### Trend Following
- Simple Moving Averages (20, 50, 200)
- Exponential Moving Averages (12, 26)
- MACD (12, 26, 9)
- ADX (14)
- Parabolic SAR

### Momentum/Oscillators
- RSI (14)
- Stochastic (14, 3, 3)
- Williams %R (14)
- CCI (20)
- ROC (12)

### Volatility
- Bollinger Bands (20, 2)
- ATR (14)
- Bollinger Band Width
- %B indicator

### Volume
- Volume SMA (20)
- OBV (On Balance Volume)
- Volume Rate of Change
- VWAP

## Testing

Run tests with pytest:
```bash
pytest tests/
```

## Database Schema

### Tables
- **stocks**: Stock master data (code, name, sector, subsector)
- **price_data**: OHLCV data for all stocks
- **indicators**: Pre-calculated technical indicators
- **signals**: Detected trading signals

### Indexes
- Optimized for stock_id and date queries
- Signal filtering by type and strength
- Fast lookups for recent data

## Logging

Logs are stored in `logs/screener.log` with automatic rotation.

Log levels: DEBUG, INFO, WARNING, ERROR

Configure logging in `config/settings.yaml`

## Performance Considerations

- Batch processing for multiple stocks
- Database indexes for fast queries
- Incremental updates (only fetch new data)
- Rate limiting to respect API limits
- Parallel processing (configurable)

## Troubleshooting

### SSL Certificate Issues
The IDX stock list API uses a self-signed certificate. SSL verification is disabled in the configuration (`verify_ssl: false`).

### Rate Limiting
Use the `--delay` parameter when updating all stocks to avoid overwhelming the server.

### Missing Data
Some stocks may have gaps in price data due to market holidays or trading suspensions. The validator can detect these gaps.

## Contributing

This is a personal project. For issues or suggestions, please modify the code directly.

## License

Private project - All rights reserved

## Contact

For questions or issues, refer to the technical documentation in `.claude/TECHNICAL_SIGNAL_PLAN.md`

---

**Version**: 1.0.0
**Last Updated**: 2025-10-31
**Status**: Phase 1 Complete
