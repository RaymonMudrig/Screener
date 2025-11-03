# Intraday Stock Screener - Quick Setup Guide

## Overview

This guide shows you how to set up automated intraday monitoring for your stock screener. The system will automatically refresh price data, recalculate indicators, and detect signals during trading hours.

---

## ✅ What You Get

After setup, your system will:
- 📊 **Auto-fetch** latest stock prices every 15-30 minutes
- 🔢 **Auto-calculate** 40+ technical indicators
- 🎯 **Auto-detect** 25+ trading signals
- 📈 **Monitor** 1,400+ IDX stocks in real-time
- 📝 **Log** all activities for review

---

## 🚀 Quick Start (3 Methods)

### Method 1: Manual Trigger (Simplest)

**From command line:**
```bash
python3 -m src.api.cli refresh-intraday --delay 1.0
```

**From external program (Java, Node.js, Python, etc.):**
```bash
./scripts/intraday_refresh.sh --delay 1.0
```

**Estimated time:** 30-40 minutes for all stocks

---

### Method 2: Python Scheduler (Recommended)

**Auto-runs every 15 minutes during trading hours**

1. **Install dependency:**
   ```bash
   pip install apscheduler
   ```

2. **Start scheduler:**
   ```bash
   python3 scripts/scheduler_intraday.py
   ```

3. **Keep running:**
   - Leave terminal open, or
   - Run in background: `nohup python3 scripts/scheduler_intraday.py &`
   - Or use systemd/supervisor (Linux) or launchd (Mac)

**Schedule:**
- Intraday: Every 15 minutes (09:00-16:00 WIB, Mon-Fri)
- End-of-day: 16:30 WIB

**Logs:** `logs/scheduler.log`

---

### Method 3: Cron Job (Linux/Mac)

**For servers running 24/7**

1. **Edit crontab:**
   ```bash
   crontab -e
   ```

2. **Add this line:**
   ```cron
   # Intraday refresh every 15 minutes during trading hours (09:00-16:00 WIB)
   */15 9-16 * * 1-5 cd /path/to/Screener && /path/to/scripts/intraday_refresh.sh --delay 1.0
   ```

3. **Replace `/path/to/Screener`** with your actual project path

4. **Save and exit**

**Logs:** `logs/intraday_YYYYMMDD.log`

---

## 📋 Command Options

### Basic Command
```bash
python3 -m src.api.cli refresh-intraday
```

### With Custom Delay (faster)
```bash
python3 -m src.api.cli refresh-intraday --delay 0.5
```

### Test Mode (10 stocks only)
```bash
python3 -m src.api.cli refresh-intraday --limit 10 --delay 0.5
```

### Skip Price Update (only recalculate)
```bash
python3 -m src.api.cli refresh-intraday --skip-price-update
```

---

## 🔧 Integration Examples

### Call from Java

```java
ProcessBuilder pb = new ProcessBuilder(
    "/path/to/Screener/scripts/intraday_refresh.sh",
    "--delay", "1.0"
);
pb.directory(new File("/path/to/Screener"));
Process process = pb.start();
int exitCode = process.waitFor();
```

### Call from Node.js

```javascript
const { exec } = require('child_process');

exec('./scripts/intraday_refresh.sh --delay 1.0', {
    cwd: '/path/to/Screener'
}, (error, stdout, stderr) => {
    if (error) {
        console.error(`Error: ${error.message}`);
        return;
    }
    console.log(stdout);
});
```

### Call from Python

```python
import subprocess

result = subprocess.run(
    ['python3', '-m', 'src.api.cli', 'refresh-intraday', '--delay', '1.0'],
    cwd='/path/to/Screener',
    capture_output=True,
    text=True
)

print(result.stdout)
```

### Call from PHP

```php
<?php
chdir('/path/to/Screener');
$output = shell_exec('./scripts/intraday_refresh.sh --delay 1.0 2>&1');
echo $output;
?>
```

---

## 📊 What Happens During Refresh

### Step 1: Update Prices (60-70% of time)
- Fetches latest data from IDX API
- Updates only new records (incremental)
- Handles rate limiting automatically

### Step 2: Calculate Indicators (20-25% of time)
- Recalculates 40+ indicators
- Updates database with new values
- Skips stocks with insufficient data

### Step 3: Detect Signals (5-10% of time)
- Runs 25+ signal detectors
- Scores signals 0-100 (strength)
- Stores top opportunities

### Result
- Updated signals available via:
  - `python3 -m src.api.cli top-opportunities`
  - `python3 -m src.api.cli show-signals`

---

## 🎯 Recommended Schedules

### Conservative (Safe)
```
09:30 - Market open + 30 min
11:00 - Mid-morning
13:30 - After lunch
15:00 - Before close
16:30 - End of day
```

**Delay:** 1.5 seconds
**Total refreshes per day:** 5
**API calls per day:** ~7,000

### Balanced (Recommended)
```
Every 30 minutes: 09:30, 10:00, 10:30, ..., 16:00
End of day: 16:30
```

**Delay:** 1.0 seconds
**Total refreshes per day:** 14
**API calls per day:** ~20,000

### Aggressive (Active Trading)
```
Every 15 minutes: 09:00, 09:15, 09:30, ..., 16:00
End of day: 16:30
```

**Delay:** 0.5 seconds
**Total refreshes per day:** 29
**API calls per day:** ~40,000

---

## 📁 Output & Logs

### Log Files
```
logs/
├── scheduler.log         # Python scheduler log
├── intraday_20251031.log # Daily refresh log (bash script)
└── screener.log          # General application log
```

### Database Updates
```
database/stockCode.sqlite
├── price_data     # Updated with latest prices
├── indicators     # Recalculated values
└── signals        # New detected signals
```

### View Results
```bash
# Top opportunities
python3 -m src.api.cli top-opportunities --limit 20

# All signals
python3 -m src.api.cli show-signals --min-strength 70

# Database stats
python3 -m src.api.cli stats
```

---

## ⚡ Performance Tuning

### Faster Refreshes

**1. Reduce delay (but watch API limits):**
```bash
python3 -m src.api.cli refresh-intraday --delay 0.3
```

**2. Skip price update if already current:**
```bash
python3 -m src.api.cli refresh-intraday --skip-price-update
```

**3. Use parallel processing (future enhancement)**

### Slower/Safer Refreshes

**1. Increase delay:**
```bash
python3 -m src.api.cli refresh-intraday --delay 2.0
```

**2. Run less frequently:**
```cron
# Every 30 minutes instead of 15
0,30 9-16 * * 1-5 ...
```

---

## 🐛 Troubleshooting

### Issue: "Rate limit exceeded"
**Solution:** Increase `--delay` to 2.0 or higher

### Issue: "Database locked"
**Solution:** Another process is using the database. Wait or kill it.

### Issue: Command takes too long
**Solution:**
- Check network connection
- Try with `--limit 10` to isolate the issue
- Increase delay to avoid timeouts

### Issue: "No signals detected"
**Solution:** This is normal! Not all stocks have signals at all times.

### Issue: Script stops in background
**Solution:** Use `nohup` or process manager:
```bash
nohup python3 scripts/scheduler_intraday.py > /dev/null 2>&1 &
```

---

## 📚 Documentation

For more details, see:

- **Complete guide:** `INTRADAY_REFRESH.md`
- **All CLI commands:** `QUICK_REFERENCE.md`
- **System overview:** `PHASE3_COMPLETE.md`
- **Indicators:** `PHASE2_COMPLETE.md`

---

## 🎓 Example Workflow

### First-Time Setup
```bash
# 1. Initialize database
python3 -m src.api.cli init

# 2. Fetch all stocks
python3 -m src.api.cli update-stocks

# 3. Fetch historical prices (one-time, takes ~45 min)
python3 scripts/batch_update.py --delay 1.5

# 4. Calculate indicators (one-time, takes ~2 min)
python3 -m src.api.cli calculate-all-indicators

# 5. Detect initial signals (one-time, takes ~1 min)
python3 -m src.api.cli detect-all-signals

# 6. Start automated monitoring
python3 scripts/scheduler_intraday.py
```

### Daily Usage
```bash
# Option A: Let scheduler handle everything automatically
python3 scripts/scheduler_intraday.py

# Option B: Manual refresh when needed
python3 -m src.api.cli refresh-intraday --delay 1.0

# View results
python3 -m src.api.cli top-opportunities --limit 20
```

---

## ✅ Verification

**Check if system is working:**

```bash
# 1. Check database stats
python3 -m src.api.cli stats

# Expected output:
# Active Stocks:      1427
# Price Records:      265000+
# Indicator Records:  6800000+
# Active Signals:     100-5000

# 2. View recent signals
python3 -m src.api.cli show-signals --limit 10

# 3. Check latest price date
python3 -m src.api.cli stats | grep "Latest Price Date"
# Should be today's date during trading hours
```

---

## 🎯 Next Steps

1. **Start small:** Test with `--limit 10` first
2. **Monitor logs:** Watch for errors
3. **Adjust timing:** Find optimal refresh frequency
4. **Automate:** Set up scheduler or cron job
5. **Integrate:** Connect to your trading dashboard/alerts

---

**Version:** 1.0.0
**Created:** 2025-10-31
**Status:** Production Ready ✅
