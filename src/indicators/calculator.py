"""
Indicator Calculator Engine
Orchestrates calculation of all technical indicators
"""

import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from .trend import TrendIndicators
from .momentum import MomentumIndicators
from .volatility import VolatilityIndicators
from .volume import VolumeIndicators
from ..utils.db import DatabaseManager
from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class IndicatorCalculator:
    """Calculate and store technical indicators for stocks"""

    def __init__(self, db_path: str = None):
        self.config = get_config()

        if db_path is None:
            db_path = self.config.get('database.path', 'database/stockCode.sqlite')

        self.db = DatabaseManager(db_path)

    def calculate_indicators_for_stock(
        self,
        stock_id: str,
        start_date: str = None,
        end_date: str = None,
        store: bool = True
    ) -> pd.DataFrame:
        """
        Calculate all indicators for a stock

        Args:
            stock_id: Stock code
            start_date: Start date for calculation
            end_date: End date for calculation
            store: Whether to store indicators in database

        Returns:
            DataFrame with all indicators
        """
        logger.info(f"Calculating indicators for {stock_id}")

        # Get price data from database
        price_data = self.db.get_price_data(stock_id, start_date, end_date)

        if not price_data:
            logger.warning(f"No price data found for {stock_id}")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(price_data)

        # Ensure numeric types
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])

        # Set date as index
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df.set_index('date')

        # Need minimum data points for indicators
        if len(df) < 50:
            logger.warning(f"Insufficient data for {stock_id}: {len(df)} records")
            return df

        # Calculate all indicators
        logger.debug(f"Calculating trend indicators for {stock_id}")
        df = TrendIndicators.calculate_all_trend_indicators(df, self.config.indicators)

        logger.debug(f"Calculating momentum indicators for {stock_id}")
        df = MomentumIndicators.calculate_all_momentum_indicators(df, self.config.indicators)

        logger.debug(f"Calculating volatility indicators for {stock_id}")
        df = VolatilityIndicators.calculate_all_volatility_indicators(df, self.config.indicators)

        logger.debug(f"Calculating volume indicators for {stock_id}")
        df = VolumeIndicators.calculate_all_volume_indicators(df, self.config.indicators)

        logger.info(f"Calculated {len(df.columns)} total columns for {stock_id}")

        # Store indicators in database
        if store:
            self._store_indicators(stock_id, df)

        return df

    def _store_indicators(self, stock_id: str, df: pd.DataFrame) -> int:
        """
        Store calculated indicators in database

        Args:
            stock_id: Stock code
            df: DataFrame with indicators

        Returns:
            Number of indicator records stored
        """
        # Get list of indicator columns (exclude OHLCV and id columns)
        ohlcv_columns = ['id', 'stock_id', 'open', 'high', 'low', 'close', 'volume']
        indicator_columns = [col for col in df.columns if col not in ohlcv_columns]

        logger.debug(f"Storing {len(indicator_columns)} indicators for {stock_id}")

        # Prepare bulk insert data
        bulk_data = []

        for date, row in df.iterrows():
            date_str = date.strftime('%Y-%m-%d')

            for indicator_name in indicator_columns:
                value = row[indicator_name]

                # Skip NaN values
                if pd.isna(value):
                    continue

                # Convert to float
                value = float(value)

                bulk_data.append((
                    stock_id,
                    date_str,
                    indicator_name,
                    value,
                    None  # metadata
                ))

        # Store in database
        if bulk_data:
            count = self.db.insert_indicators_bulk(bulk_data)
            logger.info(f"Stored {count} indicator records for {stock_id}")
            return count

        return 0

    def calculate_indicators_for_all_stocks(
        self,
        limit: int = None,
        skip_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate indicators for all stocks

        Args:
            limit: Limit number of stocks to process
            skip_existing: Skip stocks that already have indicators

        Returns:
            Statistics dictionary
        """
        logger.info("Calculating indicators for all stocks")

        # Get all active stocks
        stocks = self.db.get_all_stocks(active_only=True)

        if limit:
            stocks = stocks[:limit]

        logger.info(f"Processing {len(stocks)} stocks")

        stats = {
            'total_stocks': len(stocks),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_indicators': 0
        }

        for i, stock in enumerate(stocks):
            stock_id = stock['stock_id']
            logger.info(f"Processing {i+1}/{len(stocks)}: {stock_id}")

            try:
                # Check if indicators already exist
                if skip_existing:
                    existing = self.db.get_indicators(stock_id, limit=1)
                    if existing:
                        logger.info(f"Skipping {stock_id} (indicators already exist)")
                        stats['skipped'] += 1
                        continue

                # Calculate indicators
                df = self.calculate_indicators_for_stock(stock_id)

                if not df.empty:
                    stats['successful'] += 1
                    # Estimate indicator count (rows * indicator columns)
                    indicator_cols = len([c for c in df.columns if c not in ['id', 'stock_id', 'open', 'high', 'low', 'close', 'volume']])
                    stats['total_indicators'] += len(df) * indicator_cols
                else:
                    stats['failed'] += 1

            except Exception as e:
                logger.error(f"Failed to calculate indicators for {stock_id}: {e}")
                stats['failed'] += 1

        logger.info(
            f"Indicator calculation completed: {stats['successful']} successful, "
            f"{stats['failed']} failed, {stats['skipped']} skipped"
        )

        return stats

    def get_latest_indicators(self, stock_id: str) -> Dict[str, float]:
        """
        Get latest indicator values for a stock

        Args:
            stock_id: Stock code

        Returns:
            Dictionary of indicator_name: value
        """
        # Get indicators from database (most recent date)
        indicators = self.db.execute_query("""
            SELECT indicator_name, value, date
            FROM indicators
            WHERE stock_id = ?
            AND date = (
                SELECT MAX(date)
                FROM indicators
                WHERE stock_id = ?
            )
        """, (stock_id, stock_id))

        result = {}
        for row in indicators:
            result[row['indicator_name']] = row['value']

        return result

    def get_indicator_history(
        self,
        stock_id: str,
        indicator_name: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical values for a specific indicator

        Args:
            stock_id: Stock code
            indicator_name: Name of indicator
            limit: Number of historical values

        Returns:
            List of {date, value} dicts
        """
        return self.db.get_indicators(
            stock_id,
            indicator_name=indicator_name,
            limit=limit
        )
