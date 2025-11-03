# Intraday Data Refresh Guide

## Overview

The `refresh-intraday` command provides automated intraday monitoring by:
1. **Fetching latest prices** for all stocks
2. **Recalculating indicators** based on new price data
3. **Detecting new signals** based on updated indicators

This command is designed to be triggered by external programs (e.g., cron jobs, schedulers) during trading hours.

---

## Command Usage

### Basic Usage

```bash
python3 -m src.api.cli refresh-intraday
```

This will:
- Update prices for all 1,400+ stocks
- Recalculate all indicators
- Detect all signals
- Takes approximately 30-40 minutes (with 1s delay)

### Command Options

```bash
python3 -m src.api.cli refresh-intraday [OPTIONS]

Options:
  --delay FLOAT              Delay between stock updates in seconds (default: 1.0)
  --limit INTEGER            Limit number of stocks for testing (optional)
  --skip-price-update        Skip price update, only recalculate indicators/signals
  --db-path TEXT             Database file path (optional)
  --help                     Show this message and exit
```

### Examples

**Fast refresh (30-second delay):**
```bash
python3 -m src.api.cli refresh-intraday --delay 0.5
```

**Test with 10 stocks:**
```bash
python3 -m src.api.cli refresh-intraday --limit 10 --delay 0.5
```

**Only recalculate indicators and signals (skip price fetch):**
```bash
python3 -m src.api.cli refresh-intraday --skip-price-update
```

---

## Scheduling Options

### Option 1: Cron Job (Linux/Mac)

Edit crontab:
```bash
crontab -e
```

Add entries for intraday updates (every 15 minutes during trading hours):
```cron
# Indonesian Stock Exchange trading hours: 09:00 - 16:00 WIB (GMT+7)
# Run every 15 minutes during trading hours
*/15 9-15 * * 1-5 cd /path/to/Screener && source .venv/bin/activate && python3 -m src.api.cli refresh-intraday --delay 0.5 >> logs/intraday.log 2>&1

# End of day full refresh (16:30)
30 16 * * 1-5 cd /path/to/Screener && source .venv/bin/activate && python3 -m src.api.cli refresh-intraday --delay 1.0 >> logs/eod.log 2>&1
```

### Option 2: Python APScheduler

See `scripts/scheduler_intraday.py` for a Python-based scheduler.

### Option 3: Task Scheduler (Windows)

1. Open Task Scheduler
2. Create New Task
3. Trigger: Daily at 09:00, repeat every 15 minutes for 7 hours
4. Action: Run `python3 -m src.api.cli refresh-intraday`
5. Conditions: Only run on weekdays

### Option 4: External Program Call

From your external program (Java, Node.js, etc.):

**Python:**
```python
import subprocess

result = subprocess.run([
    'python3', '-m', 'src.api.cli', 'refresh-intraday',
    '--delay', '1.0'
], cwd='/path/to/Screener', capture_output=True, text=True)

print(result.stdout)
```

**Node.js:**
```javascript
const { execSync } = require('child_process');

const output = execSync(
    'python3 -m src.api.cli refresh-intraday --delay 1.0',
    { cwd: '/path/to/Screener', encoding: 'utf-8' }
);

console.log(output);
```

**Bash:**
```bash
#!/bin/bash
cd /path/to/Screener
source .venv/bin/activate
python3 -m src.api.cli refresh-intraday --delay 1.0
```

---

## Workflow Details

### Step 1: Update Prices

- Fetches latest price data for each stock from IDX API
- Uses incremental updates (only fetches data after last DB date)
- Respects rate limiting with configurable delay
- Ensures minimum 365-day history for indicator calculations

### Step 2: Recalculate Indicators

- Recalculates all 40+ technical indicators
- Only processes stocks with sufficient data (200+ days)
- Stores results in database (replaces old indicator values)

### Step 3: Detect Signals

- Deactivates old signals (>5 days by default)
- Detects 25+ signal types across all categories:
  - Trend signals (Golden Cross, MACD, etc.)
  - Momentum signals (RSI, Stochastic, etc.)
  - Volatility signals (Bollinger Bands, ATR, etc.)
  - Volume signals (Volume Breakout, OBV, etc.)
- Stores new signals with strength scores (0-100)

---

## Performance Metrics

**For ~1,400 stocks:**

| Delay Setting | Total Time | Use Case |
|---------------|------------|----------|
| 0.5 seconds   | ~20-25 min | Rapid intraday updates |
| 1.0 seconds   | ~30-40 min | Balanced (recommended) |
| 1.5 seconds   | ~45-60 min | Conservative rate limiting |

**Breakdown:**
- Price updates: 60-70% of total time
- Indicator calculation: 20-25% of total time
- Signal detection: 5-10% of total time

**With `--skip-price-update`:**
- Total time: ~5-10 minutes
- Use when prices are already current

---

## Output Format

The command provides real-time progress updates and a final summary:

```
=== Intraday Data Refresh ===
Started at: 2025-10-31 09:00:00

Step 1/3: Updating prices...
  [1/1427] ✓ AALI (1 records)
  [2/1427] ✓ BBCA (1 records)
  ...
  [100/1427] Already up to date

Price update: 1420 succeeded, 7 failed

Step 2/3: Recalculating indicators...
  [50/1427] Processed...
  [100/1427] Processed...
  ...

Indicator calculation: 1420 succeeded, 7 failed

Step 3/3: Detecting signals...
Deactivated 234 old signals

  [50/1427] Processed... (3 signals)
  [100/1427] Processed... (1 signals)
  ...

Signal detection: 1420 succeeded, 7 failed

=== Refresh Complete ===
Duration: 1234.5 seconds

Prices:     1420 updated, 7 failed
Indicators: 1420 updated, 7 failed
Signals:    487 new signals detected

=== Database Statistics ===
Active Stocks:      1427
Price Records:      265123
Indicator Records:  6893456
Active Signals:     487
Latest Price Date:  2025-10-31
```

---

## Best Practices

### Recommended Schedule

**During Trading Hours (09:00-16:00 WIB):**
```
09:30 - First refresh after market open
10:00 - Every 15-30 minutes
11:00
11:30
13:00 - After lunch break
13:30
14:00
14:30
15:00
15:30
16:30 - End of day full refresh
```

### Tips

1. **Start conservatively** - Use 1.5s delay initially to avoid API rate limits
2. **Monitor logs** - Check for errors and adjust delay as needed
3. **Test first** - Use `--limit 10` to test before full runs
4. **Off-hours** - Run full refresh overnight for historical data backfill
5. **Disk space** - Monitor database size (grows ~1-2 MB per day)
6. **Skip price updates** - Use `--skip-price-update` if prices already current

### Error Handling

The command is resilient to errors:
- Individual stock failures don't stop the process
- Failed stocks are logged and counted
- Database transactions are protected
- Rate limit errors are caught and logged

### Monitoring

Check command success:
```bash
# Check exit code
echo $?  # 0 = success

# Monitor log file
tail -f logs/intraday.log

# Check database stats
python3 -m src.api.cli stats
```

---

## Integration Examples

### Example: Trigger on Market Open

```python
#!/usr/bin/env python3
"""
Run intraday refresh at market open and every 15 minutes
"""
from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def refresh_data():
    logger.info("Starting intraday refresh...")
    result = subprocess.run(
        ['python3', '-m', 'src.api.cli', 'refresh-intraday', '--delay', '1.0'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        logger.info("Refresh completed successfully")
    else:
        logger.error(f"Refresh failed: {result.stderr}")

scheduler = BlockingScheduler()

# Run every 15 minutes during trading hours (Mon-Fri, 9:00-16:00)
scheduler.add_job(
    refresh_data,
    'cron',
    day_of_week='mon-fri',
    hour='9-15',
    minute='0,15,30,45'
)

# End of day refresh
scheduler.add_job(
    refresh_data,
    'cron',
    day_of_week='mon-fri',
    hour=16,
    minute=30
)

logger.info("Scheduler started. Waiting for trading hours...")
scheduler.start()
```

### Example: Web Trigger

```python
from flask import Flask, jsonify
import subprocess
import threading

app = Flask(__name__)

@app.route('/refresh', methods=['POST'])
def trigger_refresh():
    """API endpoint to trigger refresh"""
    def run_refresh():
        subprocess.run([
            'python3', '-m', 'src.api.cli',
            'refresh-intraday', '--delay', '1.0'
        ])

    # Run in background thread
    thread = threading.Thread(target=run_refresh)
    thread.start()

    return jsonify({'status': 'started', 'message': 'Refresh initiated'})

if __name__ == '__main__':
    app.run(port=5000)
```

---

## Troubleshooting

### Issue: "SSL Certificate Error"

The IDX API uses self-signed certificates. This is handled automatically by the fetcher.

### Issue: "Rate Limit Exceeded"

Increase the `--delay` parameter:
```bash
python3 -m src.api.cli refresh-intraday --delay 2.0
```

### Issue: "Database Locked"

Another process is accessing the database. Wait for it to complete or close it.

### Issue: "Insufficient Data" Warnings

Normal for stocks with short trading history. They'll be skipped automatically.

### Issue: Command Hangs

- Check network connection
- Check if API is accessible
- Try with `--limit 5` to isolate the issue

---

## Related Commands

```bash
# View top opportunities after refresh
python3 -m src.api.cli top-opportunities --limit 20

# Check specific signals
python3 -m src.api.cli show-signals --signal-type trend --min-strength 80

# Database statistics
python3 -m src.api.cli stats
```

---

**Version**: 1.0.0
**Last Updated**: 2025-10-31
**Command**: `refresh-intraday`
