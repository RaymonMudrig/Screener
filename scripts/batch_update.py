#!/usr/bin/env python3
"""
Batch update script for stock screener
Fetches stock list and updates price data for all stocks
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.storage import DataStorage
from src.utils.logger import get_logger

logger = get_logger(__name__)


def batch_update(limit=None, delay=1.5, days=365, skip_stock_list=False):
    """
    Perform batch update of all stocks

    Args:
        limit: Limit number of stocks to update (for testing)
        delay: Delay between stock updates in seconds
        days: Number of days of history to fetch
        skip_stock_list: Skip fetching stock list if already updated
    """
    storage = DataStorage()

    print("=" * 80)
    print("BATCH UPDATE - Indonesian Stock Exchange Data")
    print("=" * 80)
    print()

    # Step 1: Update stock list
    if not skip_stock_list:
        print("Step 1: Fetching stock list from IDX...")
        print("-" * 80)
        try:
            count = storage.update_stock_list()
            print(f"✓ Successfully fetched {count} stocks from IDX")
            print()
        except Exception as e:
            print(f"✗ Error fetching stock list: {e}")
            logger.exception("Failed to fetch stock list")
            return False
    else:
        print("Step 1: Skipping stock list update (using existing data)")
        print()

    # Step 2: Get list of stocks to update
    print("Step 2: Preparing batch update...")
    print("-" * 80)

    stocks = storage.get_all_stocks()
    if limit:
        stocks = stocks[:limit]
        print(f"Limiting to {limit} stocks for testing")

    print(f"Total stocks to update: {len(stocks)}")
    print(f"Delay between requests: {delay} seconds")
    print(f"Days of history: {days}")
    print()

    # Estimate time
    estimated_time = len(stocks) * (delay + 2)  # +2 for processing time
    estimated_minutes = estimated_time / 60
    print(f"Estimated time: {estimated_minutes:.1f} minutes")
    print()

    # Confirm
    if not limit and len(stocks) > 20:
        response = input(f"About to update {len(stocks)} stocks. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled by user")
            return False

    # Step 3: Batch update
    print("\nStep 3: Batch updating price data...")
    print("-" * 80)

    start_time = datetime.now()
    stats = storage.update_all_price_data(limit=limit, delay=delay)
    end_time = datetime.now()

    elapsed = (end_time - start_time).total_seconds()
    elapsed_minutes = elapsed / 60

    # Results
    print()
    print("=" * 80)
    print("BATCH UPDATE COMPLETE")
    print("=" * 80)
    print(f"Total stocks:        {stats['total_stocks']}")
    print(f"Successful:          {stats['successful']}")
    print(f"Failed:              {stats['failed']}")
    print(f"Total records:       {stats['total_records']:,}")
    print(f"Elapsed time:        {elapsed_minutes:.1f} minutes")
    print()

    # Database stats
    print("Database Statistics:")
    print("-" * 80)
    db_stats = storage.get_stats()
    print(f"Active stocks:       {db_stats.get('active_stocks', 0)}")
    print(f"Price records:       {db_stats.get('price_records', 0):,}")
    print(f"Latest price date:   {db_stats.get('latest_price_date', 'N/A')}")
    print()

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Batch update stock data from IDX",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 10 stocks
  python3 scripts/batch_update.py --limit 10

  # Update all stocks with 2-second delay
  python3 scripts/batch_update.py --delay 2.0

  # Update last 30 days only
  python3 scripts/batch_update.py --days 30

  # Skip stock list update (use existing)
  python3 scripts/batch_update.py --skip-stock-list
        """
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of stocks to update (for testing)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=1.5,
        help='Delay between stock updates in seconds (default: 1.5)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days of history to fetch (default: 365)'
    )

    parser.add_argument(
        '--skip-stock-list',
        action='store_true',
        help='Skip fetching stock list (use existing data)'
    )

    args = parser.parse_args()

    try:
        success = batch_update(
            limit=args.limit,
            delay=args.delay,
            days=args.days,
            skip_stock_list=args.skip_stock_list
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nBatch update interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logger.exception("Batch update failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
