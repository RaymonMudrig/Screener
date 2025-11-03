#!/usr/bin/env python3
"""
Intraday Stock Screener Scheduler

Automatically refreshes stock data during Indonesian Stock Exchange trading hours.
Trading hours: 09:00 - 16:00 WIB (GMT+7), Monday-Friday

Usage:
    python3 scripts/scheduler_intraday.py

Features:
- Runs every 15 minutes during trading hours
- End-of-day full refresh at 16:30
- Automatic logging
- Error handling and notifications
"""

import subprocess
import logging
import sys
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Setup logging
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
PYTHON_CMD = 'python3'
REFRESH_CMD = [PYTHON_CMD, '-m', 'src.api.cli', 'refresh-intraday']

# Scheduler settings
INTRADAY_DELAY = '1.0'  # Delay between stock updates (seconds)
EOD_DELAY = '1.5'       # End-of-day delay (more conservative)


def run_refresh(delay: str = INTRADAY_DELAY, job_type: str = 'intraday'):
    """
    Run the intraday refresh command

    Args:
        delay: Delay between stock updates in seconds
        job_type: Type of job (intraday or eod)
    """
    logger.info(f"=" * 60)
    logger.info(f"Starting {job_type} refresh at {datetime.now()}")
    logger.info(f"Delay: {delay}s between stocks")
    logger.info(f"=" * 60)

    try:
        cmd = REFRESH_CMD + ['--delay', delay]

        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        if result.returncode == 0:
            logger.info(f"✓ {job_type} refresh completed successfully")

            # Parse and log summary from output
            for line in result.stdout.split('\n'):
                if 'Refresh Complete' in line or 'Duration:' in line or 'Signals:' in line:
                    logger.info(f"  {line.strip()}")

        else:
            logger.error(f"✗ {job_type} refresh failed with exit code {result.returncode}")
            logger.error(f"Error output: {result.stderr[:500]}")

    except subprocess.TimeoutExpired:
        logger.error(f"✗ {job_type} refresh timed out after 1 hour")
    except Exception as e:
        logger.error(f"✗ {job_type} refresh failed with exception: {str(e)}")

    logger.info("")


def intraday_refresh():
    """Quick intraday refresh (every 15 minutes)"""
    run_refresh(delay=INTRADAY_DELAY, job_type='intraday')


def eod_refresh():
    """End-of-day comprehensive refresh"""
    run_refresh(delay=EOD_DELAY, job_type='end-of-day')


def test_refresh():
    """Test refresh with limited stocks"""
    logger.info("Running test refresh (10 stocks)...")

    try:
        cmd = REFRESH_CMD + ['--limit', '10', '--delay', '0.5']

        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for test
        )

        if result.returncode == 0:
            logger.info("✓ Test refresh successful")
            print(result.stdout)
            return True
        else:
            logger.error("✗ Test refresh failed")
            print(result.stderr)
            return False

    except Exception as e:
        logger.error(f"✗ Test refresh exception: {str(e)}")
        return False


def main():
    """Main scheduler entry point"""
    logger.info("=" * 60)
    logger.info("Intraday Stock Screener Scheduler")
    logger.info("=" * 60)
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Python: {PYTHON_CMD}")
    logger.info("")

    # Test before starting scheduler
    logger.info("Running initial test...")
    if not test_refresh():
        logger.error("Test failed! Please check configuration.")
        sys.exit(1)

    logger.info("")
    logger.info("Test passed! Starting scheduler...")
    logger.info("")

    # Create scheduler
    scheduler = BlockingScheduler()

    # Schedule intraday refreshes
    # Every 15 minutes during trading hours (09:00-16:00 WIB)
    scheduler.add_job(
        intraday_refresh,
        CronTrigger(
            day_of_week='mon-fri',
            hour='9-15',
            minute='0,15,30,45',
            timezone='Asia/Jakarta'
        ),
        id='intraday_refresh',
        name='Intraday Refresh (15min)',
        replace_existing=True
    )

    # End-of-day refresh at 16:30
    scheduler.add_job(
        eod_refresh,
        CronTrigger(
            day_of_week='mon-fri',
            hour=16,
            minute=30,
            timezone='Asia/Jakarta'
        ),
        id='eod_refresh',
        name='End-of-Day Refresh',
        replace_existing=True
    )

    # Log scheduled jobs
    logger.info("Scheduled jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} (ID: {job.id})")
        logger.info(f"    Next run: {job.next_run_time}")

    logger.info("")
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    logger.info("")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user")
        scheduler.shutdown()


if __name__ == '__main__':
    main()
