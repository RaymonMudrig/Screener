"""
Data storage module
Orchestrates data fetching, validation, and storage
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .fetcher import DataFetcher
from .validator import DataValidator
from ..utils.db import DatabaseManager
from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class DataStorage:
    """Manage data fetching, validation, and storage"""

    def __init__(self, db_path: str = None):
        self.config = get_config()

        if db_path is None:
            db_path = self.config.get('database.path', 'database/stockCode.sqlite')

        self.db = DatabaseManager(db_path)
        self.fetcher = DataFetcher()
        self.validator = DataValidator()

    def update_stock_list(self) -> int:
        """
        Fetch and update stock list in database

        Returns:
            Number of stocks updated
        """
        logger.info("Updating stock list...")

        # Fetch stock list
        stocks = self.fetcher.fetch_stock_list()

        if not stocks:
            logger.error("No stocks fetched")
            return 0

        # Store in database
        count = 0
        for stock in stocks:
            success = self.db.insert_stock(
                stock_id=stock['stock_id'],
                stock_code=stock['stock_code'],
                stock_name=stock['stock_name'],
                sector=stock['sector'],
                subsector=stock['subsector']
            )
            if success:
                count += 1

        logger.info(f"Updated {count} stocks in database")
        return count

    def update_price_data(
        self,
        stock_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
        validate: bool = True,
        min_history_days: int = None
    ) -> int:
        """
        Fetch and update price data for a stock

        Args:
            stock_id: Stock code
            start_date: Start date
            end_date: End date
            validate: Whether to validate data before storing
            min_history_days: Minimum number of historical days to ensure (default: 365)

        Returns:
            Number of records stored
        """
        logger.info(f"Updating price data for {stock_id}")

        # Set minimum history requirement
        if min_history_days is None:
            min_history_days = self.config.get('fetching.fetch_history_days', 365)

        # If no start date, check when we last updated
        if start_date is None:
            last_date = self.db.get_latest_price_date(stock_id)
            if last_date:
                # Check if we have enough historical data
                last_date_obj = datetime.strptime(last_date, '%Y-%m-%d')
                days_available = (datetime.now() - last_date_obj).days

                # Count existing records
                existing_count = len(self.db.get_price_data(stock_id))

                # If we don't have enough history, fetch from earlier date
                if existing_count < min_history_days:
                    required_start = datetime.now() - timedelta(days=min_history_days)
                    start_date = required_start
                    logger.info(f"{stock_id} has only {existing_count} records, fetching {min_history_days} days of history")
                else:
                    # Fetch from day after last update (incremental)
                    start_date = last_date_obj + timedelta(days=1)
                    logger.info(f"Last data for {stock_id}: {last_date}, fetching incremental data from {start_date.date()}")
            else:
                # No existing data - fetch full history
                start_date = datetime.now() - timedelta(days=min_history_days)
                logger.info(f"No existing data for {stock_id}, fetching {min_history_days} days")

        # Fetch price data
        price_data = self.fetcher.fetch_price_data(stock_id, start_date, end_date)

        if not price_data:
            logger.warning(f"No price data fetched for {stock_id}")
            return 0

        logger.info(f"Fetched {len(price_data)} records for {stock_id}")

        # Validate data
        if validate:
            valid_data, invalid_data = self.validator.validate_price_data(price_data, stock_id)

            if invalid_data:
                logger.warning(f"Found {len(invalid_data)} invalid records for {stock_id}")

            price_data = valid_data

        if not price_data:
            logger.warning(f"No valid price data for {stock_id}")
            return 0

        # Prepare bulk insert data
        bulk_data = [
            (
                stock_id,
                record['date'],
                record['open'],
                record['high'],
                record['low'],
                record['close'],
                record['volume']
            )
            for record in price_data
        ]

        # Store in database
        count = self.db.insert_price_data_bulk(bulk_data)

        logger.info(f"Stored {count} price records for {stock_id}")

        # Update stock's last_updated timestamp
        self.db.execute_update(
            "UPDATE stocks SET last_updated = ? WHERE stock_id = ?",
            (datetime.now(), stock_id)
        )

        return count

    def update_all_price_data(
        self,
        limit: int = None,
        delay: float = 1.0
    ) -> Dict[str, int]:
        """
        Update price data for all active stocks

        Args:
            limit: Limit number of stocks to update (for testing)
            delay: Delay between stock updates in seconds

        Returns:
            Dictionary with update statistics
        """
        logger.info("Updating price data for all stocks...")

        # Get all active stocks
        stocks = self.db.get_all_stocks(active_only=True)

        if limit:
            stocks = stocks[:limit]

        logger.info(f"Found {len(stocks)} active stocks to update")

        stats = {
            'total_stocks': len(stocks),
            'successful': 0,
            'failed': 0,
            'total_records': 0
        }

        import time

        for i, stock in enumerate(stocks):
            stock_id = stock['stock_id']
            logger.info(f"Processing {i+1}/{len(stocks)}: {stock_id}")

            try:
                count = self.update_price_data(stock_id)
                stats['total_records'] += count
                stats['successful'] += 1

            except Exception as e:
                logger.error(f"Failed to update {stock_id}: {e}")
                stats['failed'] += 1

            # Delay between requests
            if i < len(stocks) - 1:
                time.sleep(delay)

        logger.info(
            f"Update completed: {stats['successful']} successful, "
            f"{stats['failed']} failed, {stats['total_records']} total records"
        )

        return stats

    def get_price_data(
        self,
        stock_id: str,
        start_date: str = None,
        end_date: str = None,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get price data from database

        Args:
            stock_id: Stock code
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum number of records to return

        Returns:
            List of price records
        """
        return self.db.get_price_data(stock_id, start_date, end_date, limit)

    def get_stock_info(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """Get stock information"""
        return self.db.get_stock(stock_id)

    def get_all_stocks(self) -> List[Dict[str, Any]]:
        """Get all stocks"""
        return self.db.get_all_stocks()

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.db.get_database_stats()

    def generate_quality_report(self, stock_id: str) -> Dict[str, Any]:
        """
        Generate data quality report for a stock

        Args:
            stock_id: Stock code

        Returns:
            Quality report dictionary
        """
        price_data = self.get_price_data(stock_id)
        return self.validator.get_data_quality_report(price_data, stock_id)
