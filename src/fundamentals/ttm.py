"""
TTM (Trailing 12 Months) Calculator

Aggregate last 4 quarters to calculate annualized metrics
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.db import DatabaseManager

logger = get_logger(__name__)


class TTMCalculator:
    """Calculate Trailing 12 Months metrics"""

    def __init__(self, db_path: str = None):
        """Initialize TTM calculator"""
        if db_path:
            self.db = DatabaseManager(db_path)
        else:
            from ..utils.config import get_config
            config = get_config()
            db_path = config.get('database.path', 'database/stockCode.sqlite')
            self.db = DatabaseManager(db_path)

    @staticmethod
    def sum_last_4_quarters(quarters: List[Dict[str, Any]], field: str) -> Optional[float]:
        """
        Sum a field over the last 4 quarters

        Args:
            quarters: List of quarterly data (newest first)
            field: Field name to sum

        Returns:
            Sum of last 4 quarters or None
        """
        if not quarters or len(quarters) < 4:
            return None

        values = [q.get(field) for q in quarters[:4]]

        # Check if all values exist
        if None in values:
            return None

        return sum(values)

    @staticmethod
    def average_last_4_quarters(quarters: List[Dict[str, Any]], field: str) -> Optional[float]:
        """
        Average a field over the last 4 quarters

        Args:
            quarters: List of quarterly data (newest first)
            field: Field name to average

        Returns:
            Average of last 4 quarters or None
        """
        if not quarters or len(quarters) < 4:
            return None

        values = [q.get(field) for q in quarters[:4]]

        # Check if all values exist
        if None in values:
            return None

        return sum(values) / 4

    def calculate_ttm_income_statement(self, quarters: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate TTM income statement metrics

        Args:
            quarters: List of quarterly data (newest first, minimum 4 quarters)

        Returns:
            Dict with TTM metrics
        """
        if not quarters or len(quarters) < 4:
            return {}

        ttm_metrics = {}

        # Sum these over 4 quarters
        sum_fields = [
            'revenue',
            'cost_of_goods_sold',
            'gross_profit',
            'operating_profit',
            'net_income',
            'tax'
        ]

        for field in sum_fields:
            ttm_value = self.sum_last_4_quarters(quarters, field)
            if ttm_value is not None:
                ttm_metrics[f'ttm_{field}'] = ttm_value

        # Calculate EPS for TTM
        ttm_net_income = ttm_metrics.get('ttm_net_income')
        latest_shares = quarters[0].get('shares_outstanding')

        if ttm_net_income and latest_shares and latest_shares > 0:
            ttm_metrics['ttm_eps'] = ttm_net_income / latest_shares

        return ttm_metrics

    def calculate_ttm_cash_flow(self, quarters: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate TTM cash flow metrics"""
        if not quarters or len(quarters) < 4:
            return {}

        ttm_metrics = {}

        cash_flow_fields = [
            'cf_operating',
            'cf_investing',
            'cf_financing'
        ]

        for field in cash_flow_fields:
            ttm_value = self.sum_last_4_quarters(quarters, field)
            if ttm_value is not None:
                ttm_metrics[f'ttm_{field}'] = ttm_value

        return ttm_metrics

    def calculate_ttm_margins(self, quarters: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate TTM margin percentages

        Uses TTM revenue and TTM profits to calculate accurate margins
        """
        if not quarters or len(quarters) < 4:
            return {}

        ttm_metrics = {}

        # Get TTM revenue first
        ttm_revenue = self.sum_last_4_quarters(quarters, 'revenue')
        if not ttm_revenue or ttm_revenue == 0:
            return {}

        # Calculate margins
        ttm_gross_profit = self.sum_last_4_quarters(quarters, 'gross_profit')
        if ttm_gross_profit is not None:
            ttm_metrics['ttm_gross_margin'] = (ttm_gross_profit / ttm_revenue) * 100

        ttm_operating_profit = self.sum_last_4_quarters(quarters, 'operating_profit')
        if ttm_operating_profit is not None:
            ttm_metrics['ttm_operating_margin'] = (ttm_operating_profit / ttm_revenue) * 100

        ttm_net_income = self.sum_last_4_quarters(quarters, 'net_income')
        if ttm_net_income is not None:
            ttm_metrics['ttm_net_margin'] = (ttm_net_income / ttm_revenue) * 100

        return ttm_metrics

    def calculate_ttm_returns(self, quarters: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate TTM return ratios (ROE, ROA, ROIC)

        Uses TTM net income and latest balance sheet
        """
        if not quarters or len(quarters) < 4:
            return {}

        ttm_metrics = {}
        latest = quarters[0]

        # Get TTM net income
        ttm_net_income = self.sum_last_4_quarters(quarters, 'net_income')
        if not ttm_net_income:
            return {}

        # TTM ROE
        total_equity = latest.get('total_equity')
        if total_equity and total_equity > 0:
            ttm_metrics['ttm_roe'] = (ttm_net_income / total_equity) * 100

        # TTM ROA
        total_assets = latest.get('total_assets')
        if total_assets and total_assets > 0:
            ttm_metrics['ttm_roa'] = (ttm_net_income / total_assets) * 100

        # TTM ROIC
        total_liabilities = latest.get('total_liabilities', 0)
        if total_equity:
            invested_capital = total_equity + total_liabilities
            if invested_capital > 0:
                ttm_metrics['ttm_roic'] = (ttm_net_income / invested_capital) * 100

        return ttm_metrics

    def calculate_all_ttm_metrics(self, quarters: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate all TTM metrics

        Args:
            quarters: List of quarterly data (newest first, minimum 4 quarters)

        Returns:
            Dict with all TTM metrics
        """
        if not quarters or len(quarters) < 4:
            logger.warning("Need at least 4 quarters for TTM calculation")
            return {}

        all_ttm = {}

        # Income statement
        all_ttm.update(self.calculate_ttm_income_statement(quarters))

        # Cash flow
        all_ttm.update(self.calculate_ttm_cash_flow(quarters))

        # Margins
        all_ttm.update(self.calculate_ttm_margins(quarters))

        # Returns (ROE, ROA, ROIC)
        all_ttm.update(self.calculate_ttm_returns(quarters))

        logger.debug(f"Calculated {len(all_ttm)} TTM metrics")
        return all_ttm

    def store_ttm_metrics(self, stock_id: str, as_of_date: str, ttm_metrics: Dict[str, float]) -> bool:
        """
        Store TTM metrics in database

        Args:
            stock_id: Stock code
            as_of_date: Date of latest quarter
            ttm_metrics: Dictionary of TTM metrics

        Returns:
            True if successful
        """
        query = """
            INSERT OR REPLACE INTO ttm_metrics (
                stock_id, as_of_date,
                ttm_revenue, ttm_gross_profit, ttm_operating_profit, ttm_net_income, ttm_eps,
                ttm_gross_margin, ttm_operating_margin, ttm_net_margin,
                ttm_cf_operating, ttm_cf_investing, ttm_cf_financing,
                ttm_roe, ttm_roa, ttm_roic
            ) VALUES (
                ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?
            )
        """

        params = (
            stock_id, as_of_date,
            ttm_metrics.get('ttm_revenue'),
            ttm_metrics.get('ttm_gross_profit'),
            ttm_metrics.get('ttm_operating_profit'),
            ttm_metrics.get('ttm_net_income'),
            ttm_metrics.get('ttm_eps'),
            ttm_metrics.get('ttm_gross_margin'),
            ttm_metrics.get('ttm_operating_margin'),
            ttm_metrics.get('ttm_net_margin'),
            ttm_metrics.get('ttm_cf_operating'),
            ttm_metrics.get('ttm_cf_investing'),
            ttm_metrics.get('ttm_cf_financing'),
            ttm_metrics.get('ttm_roe'),
            ttm_metrics.get('ttm_roa'),
            ttm_metrics.get('ttm_roic')
        )

        try:
            self.db.execute_update(query, params)
            logger.debug(f"Stored TTM metrics for {stock_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing TTM metrics for {stock_id}: {e}")
            return False

    def calculate_and_store_ttm(self, stock_id: str, quarters: List[Dict[str, Any]]) -> bool:
        """
        Calculate and store TTM metrics for a stock

        Args:
            stock_id: Stock code
            quarters: List of quarterly data

        Returns:
            True if successful
        """
        if not quarters or len(quarters) < 4:
            logger.warning(f"Insufficient quarters for {stock_id}: {len(quarters) if quarters else 0}")
            return False

        # Calculate TTM
        ttm_metrics = self.calculate_all_ttm_metrics(quarters)

        if not ttm_metrics:
            return False

        # Get latest quarter date
        as_of_date = quarters[0].get('report_date')
        if not as_of_date:
            logger.error(f"No report_date for {stock_id}")
            return False

        # Store
        return self.store_ttm_metrics(stock_id, as_of_date, ttm_metrics)

    def get_ttm_metrics(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """
        Get latest TTM metrics for a stock

        Args:
            stock_id: Stock code

        Returns:
            Dict with TTM metrics or None
        """
        query = """
            SELECT * FROM ttm_metrics
            WHERE stock_id = ?
            ORDER BY as_of_date DESC
            LIMIT 1
        """

        rows = self.db.execute_query(query, (stock_id,))
        return dict(rows[0]) if rows else None

    def calculate_ttm_for_all_stocks(self, limit: int = None) -> Dict[str, int]:
        """
        Calculate TTM metrics for all stocks

        Args:
            limit: Limit number of stocks (for testing)

        Returns:
            Statistics dictionary
        """
        # Get all stocks
        stocks = self.db.get_all_stocks(active_only=True)

        if limit:
            stocks = stocks[:limit]

        logger.info(f"Calculating TTM metrics for {len(stocks)} stocks")

        stats = {
            'total_stocks': len(stocks),
            'successful': 0,
            'failed': 0,
            'insufficient_data': 0
        }

        for i, stock in enumerate(stocks):
            stock_id = stock['stock_id']
            logger.info(f"Processing {i+1}/{len(stocks)}: {stock_id}")

            try:
                # Get last 4 quarters
                query = """
                    SELECT * FROM fundamental_data
                    WHERE stock_id = ?
                    ORDER BY year DESC, quarter DESC
                    LIMIT 4
                """

                quarters = self.db.execute_query(query, (stock_id,))
                quarters = [dict(q) for q in quarters]

                if len(quarters) < 4:
                    stats['insufficient_data'] += 1
                    continue

                # Calculate and store
                success = self.calculate_and_store_ttm(stock_id, quarters)

                if success:
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1

            except Exception as e:
                logger.error(f"Failed to calculate TTM for {stock_id}: {e}")
                stats['failed'] += 1

        logger.info(
            f"TTM calculation complete: {stats['successful']} successful, "
            f"{stats['failed']} failed, {stats['insufficient_data']} insufficient data"
        )

        return stats
