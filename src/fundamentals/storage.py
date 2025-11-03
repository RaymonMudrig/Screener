"""
Fundamental Data Storage

Handles storing and retrieving fundamental data from the database
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from ..utils.db import DatabaseManager
from ..utils.logger import get_logger
from ..utils.config import get_config
from .fetcher import FundamentalDataFetcher

logger = get_logger(__name__)


class FundamentalDataStorage:
    """Store and retrieve fundamental data"""

    def __init__(self, db_path: str = None):
        """
        Initialize storage

        Args:
            db_path: Database file path (uses default if None)
        """
        if db_path is None:
            config = get_config()
            db_path = config.get('database.path', 'database/stockCode.sqlite')

        self.db = DatabaseManager(db_path)
        self.fetcher = FundamentalDataFetcher()

    def store_quarterly_data(
        self,
        stock_id: str,
        year: int,
        quarter: int,
        data: Dict[str, Any]
    ) -> bool:
        """
        Store quarterly fundamental data

        Args:
            stock_id: Stock code
            year: Year
            quarter: Quarter 1-4
            data: Normalized fundamental data dictionary

        Returns:
            True if successful
        """
        query = """
            INSERT OR REPLACE INTO fundamental_data (
                stock_id, year, quarter, report_date, fiscal_year, month_cover,
                close_price, par_value, shares_outstanding, authorized_shares,
                receivables, inventories, current_assets, fixed_assets, other_assets,
                total_assets, non_current_assets,
                current_liabilities, long_term_liabilities, total_liabilities,
                paidup_capital, retained_earnings, total_equity, minority_interest,
                revenue, cost_of_goods_sold, gross_profit, operating_profit,
                other_income, earnings_before_tax, tax, net_income,
                cf_operating, cf_investing, cf_financing, net_cash_increase,
                cash_begin, cash_end, cash_equivalent,
                eps, book_value, pe_ratio, pb_ratio, debt_equity_ratio,
                roa_percent, roe_percent, npm_percent, opm_percent,
                gross_margin_percent, asset_turnover,
                updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                CURRENT_TIMESTAMP
            )
        """

        params = (
            stock_id, year, quarter, data.get('report_date'), data.get('fiscal_year'), data.get('month_cover'),
            data.get('close_price'), data.get('par_value'), data.get('shares_outstanding'), data.get('authorized_shares'),
            data.get('receivables'), data.get('inventories'), data.get('current_assets'),
            data.get('fixed_assets'), data.get('other_assets'), data.get('total_assets'), data.get('non_current_assets'),
            data.get('current_liabilities'), data.get('long_term_liabilities'), data.get('total_liabilities'),
            data.get('paidup_capital'), data.get('retained_earnings'), data.get('total_equity'), data.get('minority_interest'),
            data.get('revenue'), data.get('cost_of_goods_sold'), data.get('gross_profit'), data.get('operating_profit'),
            data.get('other_income'), data.get('earnings_before_tax'), data.get('tax'), data.get('net_income'),
            data.get('cf_operating'), data.get('cf_investing'), data.get('cf_financing'), data.get('net_cash_increase'),
            data.get('cash_begin'), data.get('cash_end'), data.get('cash_equivalent'),
            data.get('eps'), data.get('book_value'), data.get('pe_ratio'), data.get('pb_ratio'), data.get('debt_equity_ratio'),
            data.get('roa_percent'), data.get('roe_percent'), data.get('npm_percent'), data.get('opm_percent'),
            data.get('gross_margin_percent'), data.get('asset_turnover')
        )

        try:
            self.db.execute_update(query, params)
            logger.debug(f"Stored {stock_id} Q{quarter} {year}")
            return True

        except Exception as e:
            logger.error(f"Error storing {stock_id} Q{quarter} {year}: {e}")
            return False

    def fetch_and_store_quarter(
        self,
        stock_id: str,
        year: int,
        quarter: int
    ) -> bool:
        """
        Fetch and store quarterly data in one operation

        Args:
            stock_id: Stock code
            year: Year
            quarter: Quarter 1-4

        Returns:
            True if successful
        """
        # Fetch data
        raw_data = self.fetcher.fetch_quarterly_data(stock_id, year, quarter)
        if not raw_data:
            return False

        # Normalize
        normalized_data = self.fetcher.normalize_data(raw_data)

        # Store
        return self.store_quarterly_data(stock_id, year, quarter, normalized_data)

    def fetch_and_store_latest(self, stock_id: str) -> bool:
        """
        Fetch and store the latest quarter for a stock

        Args:
            stock_id: Stock code

        Returns:
            True if successful
        """
        # Fetch latest
        raw_data = self.fetcher.fetch_latest_quarter(stock_id)
        if not raw_data:
            return False

        # Normalize
        normalized_data = self.fetcher.normalize_data(raw_data)

        # Store
        return self.store_quarterly_data(
            normalized_data['stock_id'],
            normalized_data['year'],
            normalized_data['quarter'],
            normalized_data
        )

    def fetch_and_store_multiple(
        self,
        stock_id: str,
        num_quarters: int = 8
    ) -> int:
        """
        Fetch and store multiple quarters

        Args:
            stock_id: Stock code
            num_quarters: Number of quarters to fetch

        Returns:
            Number of quarters successfully stored
        """
        # Fetch multiple quarters
        quarters_data = self.fetcher.fetch_multiple_quarters(stock_id, num_quarters)

        stored_count = 0
        for raw_data in quarters_data:
            # Normalize
            normalized_data = self.fetcher.normalize_data(raw_data)

            # Store
            success = self.store_quarterly_data(
                normalized_data['stock_id'],
                normalized_data['year'],
                normalized_data['quarter'],
                normalized_data
            )

            if success:
                stored_count += 1

        logger.info(f"Stored {stored_count}/{len(quarters_data)} quarters for {stock_id}")
        return stored_count

    def get_quarterly_data(
        self,
        stock_id: str,
        year: int,
        quarter: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get quarterly data from database

        Args:
            stock_id: Stock code
            year: Year
            quarter: Quarter 1-4

        Returns:
            Dictionary with fundamental data or None
        """
        query = """
            SELECT * FROM fundamental_data
            WHERE stock_id = ? AND year = ? AND quarter = ?
        """

        rows = self.db.execute_query(query, (stock_id, year, quarter))
        return dict(rows[0]) if rows else None

    def get_latest_quarter(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest quarter data for a stock

        Args:
            stock_id: Stock code

        Returns:
            Latest fundamental data or None
        """
        query = """
            SELECT * FROM fundamental_data
            WHERE stock_id = ?
            ORDER BY year DESC, quarter DESC
            LIMIT 1
        """

        rows = self.db.execute_query(query, (stock_id,))
        return dict(rows[0]) if rows else None

    def get_quarters(
        self,
        stock_id: str,
        num_quarters: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get multiple quarters of data

        Args:
            stock_id: Stock code
            num_quarters: Number of quarters to retrieve

        Returns:
            List of fundamental data dictionaries (newest first)
        """
        query = """
            SELECT * FROM fundamental_data
            WHERE stock_id = ?
            ORDER BY year DESC, quarter DESC
            LIMIT ?
        """

        rows = self.db.execute_query(query, (stock_id, num_quarters))
        return [dict(row) for row in rows]

    def get_year_data(
        self,
        stock_id: str,
        year: int
    ) -> List[Dict[str, Any]]:
        """
        Get all quarters for a specific year

        Args:
            stock_id: Stock code
            year: Year

        Returns:
            List of quarterly data (Q1-Q4)
        """
        query = """
            SELECT * FROM fundamental_data
            WHERE stock_id = ? AND year = ?
            ORDER BY quarter ASC
        """

        rows = self.db.execute_query(query, (stock_id, year))
        return [dict(row) for row in rows]

    def get_all_stocks_latest(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get latest quarter for all stocks

        Args:
            active_only: Only active stocks

        Returns:
            List of latest fundamental data for each stock
        """
        # Get stock list
        stocks = self.db.get_all_stocks(active_only=active_only)

        results = []
        for stock in stocks:
            latest = self.get_latest_quarter(stock['stock_id'])
            if latest:
                results.append(latest)

        return results

    def update_all_stocks(
        self,
        num_quarters: int = 8,
        delay: float = 1.0,
        limit: int = None
    ) -> Dict[str, int]:
        """
        Update fundamental data for all stocks

        Args:
            num_quarters: Number of quarters to fetch per stock
            delay: Delay between stocks (seconds)
            limit: Limit number of stocks (for testing)

        Returns:
            Statistics dictionary
        """
        import time

        # Get all active stocks
        stocks = self.db.get_all_stocks(active_only=True)

        if limit:
            stocks = stocks[:limit]

        logger.info(f"Updating fundamental data for {len(stocks)} stocks")

        stats = {
            'total_stocks': len(stocks),
            'successful': 0,
            'failed': 0,
            'total_quarters_stored': 0
        }

        for i, stock in enumerate(stocks):
            stock_id = stock['stock_id']
            logger.info(f"Processing {i+1}/{len(stocks)}: {stock_id}")

            try:
                stored = self.fetch_and_store_multiple(stock_id, num_quarters)

                if stored > 0:
                    stats['successful'] += 1
                    stats['total_quarters_stored'] += stored
                else:
                    stats['failed'] += 1

            except Exception as e:
                logger.error(f"Failed to update {stock_id}: {e}")
                stats['failed'] += 1

            # Rate limiting
            if delay > 0 and i < len(stocks) - 1:
                time.sleep(delay)

        logger.info(
            f"Update complete: {stats['successful']} successful, "
            f"{stats['failed']} failed, {stats['total_quarters_stored']} quarters stored"
        )

        return stats

    def get_stats(self) -> Dict[str, int]:
        """Get fundamental data statistics"""
        stats = {}

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Count total records
            cursor.execute("SELECT COUNT(*) FROM fundamental_data")
            stats['total_records'] = cursor.fetchone()[0]

            # Count unique stocks
            cursor.execute("SELECT COUNT(DISTINCT stock_id) FROM fundamental_data")
            stats['stocks_with_data'] = cursor.fetchone()[0]

            # Latest quarter date
            cursor.execute("SELECT MAX(report_date) FROM fundamental_data")
            stats['latest_report_date'] = cursor.fetchone()[0]

            # Average quarters per stock
            cursor.execute("""
                SELECT AVG(quarter_count) FROM (
                    SELECT COUNT(*) as quarter_count
                    FROM fundamental_data
                    GROUP BY stock_id
                )
            """)
            result = cursor.fetchone()[0]
            stats['avg_quarters_per_stock'] = round(result, 1) if result else 0

        return stats
