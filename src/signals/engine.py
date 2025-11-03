"""
Signal Detection Engine
Orchestrates all signal detectors and manages signal storage
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

from .trend_signals import TrendSignalDetector
from .momentum_signals import MomentumSignalDetector
from .volatility_signals import VolatilitySignalDetector
from .volume_signals import VolumeSignalDetector
from .detector import Signal

from ..utils.db import DatabaseManager
from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class SignalEngine:
    """Detect and manage trading signals"""

    def __init__(self, db_path: str = None):
        self.config = get_config()

        if db_path is None:
            db_path = self.config.get('database.path', 'database/stockCode.sqlite')

        self.db = DatabaseManager(db_path)

        # Initialize signal detectors
        self.trend_detector = TrendSignalDetector(self.config.signals)
        self.momentum_detector = MomentumSignalDetector(self.config.signals)
        self.volatility_detector = VolatilitySignalDetector(self.config.signals)
        self.volume_detector = VolumeSignalDetector(self.config.signals)

    def detect_signals_for_stock(
        self,
        stock_id: str,
        df: pd.DataFrame = None,
        store: bool = True
    ) -> List[Signal]:
        """
        Detect all signals for a stock

        Args:
            stock_id: Stock code
            df: DataFrame with OHLCV and indicator data (if None, will fetch from DB)
            store: Whether to store signals in database

        Returns:
            List of detected signals
        """
        logger.info(f"Detecting signals for {stock_id}")

        # If no dataframe provided, build from database
        if df is None:
            df = self._build_dataframe(stock_id)

        if df is None or df.empty:
            logger.warning(f"No data available for {stock_id}")
            return []

        # Detect signals from all categories
        all_signals = []

        all_signals.extend(self.trend_detector.detect(df))
        all_signals.extend(self.momentum_detector.detect(df))
        all_signals.extend(self.volatility_detector.detect(df))
        all_signals.extend(self.volume_detector.detect(df))

        logger.info(f"Detected {len(all_signals)} signals for {stock_id}")

        # Store in database
        if store and all_signals:
            self._store_signals(stock_id, all_signals)

        return all_signals

    def _build_dataframe(self, stock_id: str) -> pd.DataFrame:
        """Build dataframe with price and indicator data from database"""
        # Get price data
        price_data = self.db.get_price_data(stock_id)
        if not price_data:
            return None

        df = pd.DataFrame(price_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df.set_index('date')

        # Get indicators
        indicators = self.db.get_indicators(stock_id)
        if not indicators:
            logger.warning(f"No indicators found for {stock_id}")
            return df

        # Pivot indicators into columns
        indicator_df = pd.DataFrame(indicators)
        indicator_df['date'] = pd.to_datetime(indicator_df['date'])

        # Create pivot table
        indicator_pivot = indicator_df.pivot(
            index='date',
            columns='indicator_name',
            values='value'
        )

        # Merge with price data
        df = df.join(indicator_pivot)

        return df

    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """Convert numpy types to Python types for JSON serialization"""
        import numpy as np

        sanitized = {}
        for key, value in metadata.items():
            if isinstance(value, (np.bool_, np.integer, np.floating)):
                sanitized[key] = value.item()  # Convert to Python type
            elif isinstance(value, np.ndarray):
                sanitized[key] = value.tolist()
            else:
                sanitized[key] = value
        return sanitized

    def _store_signals(self, stock_id: str, signals: List[Signal]) -> int:
        """Store signals in database"""
        count = 0

        for signal in signals:
            import json

            # Sanitize metadata to ensure JSON serializability
            metadata = {
                'direction': signal.direction.value,
                'price': signal.price,
                **signal.metadata
            }
            metadata = self._sanitize_metadata(metadata)

            success = self.db.insert_signal(
                stock_id=stock_id,
                signal_type=signal.signal_type.value,
                signal_name=signal.signal_name,
                detected_date=signal.date,
                strength=signal.strength,
                metadata=metadata
            )

            if success:
                count += 1

        logger.info(f"Stored {count} signals for {stock_id}")
        return count

    def detect_signals_for_all_stocks(
        self,
        limit: int = None,
        skip_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Detect signals for all stocks

        Args:
            limit: Limit number of stocks to process
            skip_existing: Skip stocks that already have recent signals

        Returns:
            Statistics dictionary
        """
        logger.info("Detecting signals for all stocks")

        # Get all active stocks
        stocks = self.db.get_all_stocks(active_only=True)

        if limit:
            stocks = stocks[:limit]

        logger.info(f"Processing {len(stocks)} stocks")

        # Deactivate old signals first
        expiry_days = self.config.get('signals.signal_expiry_days', 5)
        deactivated = self.db.deactivate_old_signals(expiry_days)
        logger.info(f"Deactivated {deactivated} old signals")

        stats = {
            'total_stocks': len(stocks),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_signals': 0
        }

        for i, stock in enumerate(stocks):
            stock_id = stock['stock_id']
            logger.info(f"Processing {i+1}/{len(stocks)}: {stock_id}")

            try:
                # Check if signals already exist (recent)
                if skip_existing:
                    existing = self.db.get_signals(stock_id, active_only=True, limit=1)
                    if existing:
                        logger.info(f"Skipping {stock_id} (recent signals exist)")
                        stats['skipped'] += 1
                        continue

                # Detect signals
                signals = self.detect_signals_for_stock(stock_id)

                if signals:
                    stats['successful'] += 1
                    stats['total_signals'] += len(signals)
                else:
                    stats['successful'] += 1  # No signals is still successful

            except Exception as e:
                logger.error(f"Failed to detect signals for {stock_id}: {e}")
                stats['failed'] += 1

        logger.info(
            f"Signal detection completed: {stats['successful']} successful, "
            f"{stats['failed']} failed, {stats['skipped']} skipped, "
            f"{stats['total_signals']} total signals"
        )

        return stats

    def get_signals_by_type(
        self,
        signal_type: str = None,
        min_strength: float = 50.0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get signals filtered by type and strength

        Args:
            signal_type: Signal type to filter (trend, momentum, volatility, volume)
            min_strength: Minimum signal strength
            limit: Maximum number of signals to return

        Returns:
            List of signal dictionaries
        """
        return self.db.get_signals(
            signal_type=signal_type,
            active_only=True,
            min_strength=min_strength,
            limit=limit
        )

    def get_signals_for_stock(self, stock_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all signals for a specific stock"""
        return self.db.get_signals(stock_id=stock_id, active_only=active_only)

    def get_top_opportunities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top stock opportunities based on signal strength

        Args:
            limit: Number of top opportunities to return

        Returns:
            List of opportunities with stock info and signals
        """
        # Get all active signals ordered by strength
        query = """
            SELECT
                s.stock_id,
                st.stock_name,
                s.signal_name,
                s.signal_type,
                s.strength,
                s.detected_date,
                s.metadata
            FROM signals s
            JOIN stocks st ON s.stock_id = st.stock_id
            WHERE s.is_active = TRUE
            ORDER BY s.strength DESC, s.detected_date DESC
            LIMIT ?
        """

        results = self.db.execute_query(query, (limit,))

        return [dict(row) for row in results]
