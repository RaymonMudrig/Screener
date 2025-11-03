"""
Database utilities for stock screener
Provides connection management and common database operations
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json

from .logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manage database connections and operations"""

    def __init__(self, db_path: str = "database/stockCode.sqlite"):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """Ensure database file and directory exist"""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        if not db_file.exists():
            logger.warning(f"Database does not exist at {self.db_path}. Creating...")
            # Initialize database will be called separately
            db_file.touch()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """Execute multiple queries with different parameters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount

    # Stock operations
    def insert_stock(self, stock_id: str, stock_code: str, stock_name: str = None,
                    sector: str = None, subsector: str = None) -> bool:
        """Insert or update a stock"""
        query = """
            INSERT OR REPLACE INTO stocks
            (stock_id, stock_code, stock_name, sector, subsector, last_updated, is_active)
            VALUES (?, ?, ?, ?, ?, ?, TRUE)
        """
        try:
            self.execute_update(
                query,
                (stock_id, stock_code, stock_name, sector, subsector, datetime.now())
            )
            logger.debug(f"Inserted/updated stock: {stock_code}")
            return True
        except Exception as e:
            logger.error(f"Error inserting stock {stock_code}: {e}")
            return False

    def get_all_stocks(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all stocks from database"""
        query = "SELECT * FROM stocks"
        if active_only:
            query += " WHERE is_active = TRUE"

        rows = self.execute_query(query)
        return [dict(row) for row in rows]

    def get_stock(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific stock by ID"""
        query = "SELECT * FROM stocks WHERE stock_id = ?"
        rows = self.execute_query(query, (stock_id,))
        return dict(rows[0]) if rows else None

    # Price data operations
    def insert_price_data(self, stock_id: str, date: str, open_price: float,
                         high: float, low: float, close: float, volume: int) -> bool:
        """Insert price data for a stock"""
        query = """
            INSERT OR REPLACE INTO price_data
            (stock_id, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            self.execute_update(
                query,
                (stock_id, date, open_price, high, low, close, volume)
            )
            return True
        except Exception as e:
            logger.error(f"Error inserting price data for {stock_id} on {date}: {e}")
            return False

    def insert_price_data_bulk(self, price_data_list: List[Tuple]) -> int:
        """Insert multiple price data records"""
        query = """
            INSERT OR REPLACE INTO price_data
            (stock_id, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            count = self.execute_many(query, price_data_list)
            logger.info(f"Inserted {count} price data records")
            return count
        except Exception as e:
            logger.error(f"Error bulk inserting price data: {e}")
            return 0

    def get_price_data(self, stock_id: str, start_date: str = None,
                      end_date: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get price data for a stock"""
        query = "SELECT * FROM price_data WHERE stock_id = ?"
        params = [stock_id]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        rows = self.execute_query(query, tuple(params))
        return [dict(row) for row in rows]

    def get_latest_price_date(self, stock_id: str) -> Optional[str]:
        """Get the latest date for which we have price data"""
        query = """
            SELECT MAX(date) as latest_date
            FROM price_data
            WHERE stock_id = ?
        """
        rows = self.execute_query(query, (stock_id,))
        return rows[0]['latest_date'] if rows and rows[0]['latest_date'] else None

    # Indicator operations
    def insert_indicator(self, stock_id: str, date: str, indicator_name: str,
                        value: float, metadata: Dict = None) -> bool:
        """Insert indicator value"""
        query = """
            INSERT OR REPLACE INTO indicators
            (stock_id, date, indicator_name, value, metadata)
            VALUES (?, ?, ?, ?, ?)
        """
        metadata_json = json.dumps(metadata) if metadata else None

        try:
            self.execute_update(
                query,
                (stock_id, date, indicator_name, value, metadata_json)
            )
            return True
        except Exception as e:
            logger.error(f"Error inserting indicator {indicator_name}: {e}")
            return False

    def insert_indicators_bulk(self, indicator_list: List[Tuple]) -> int:
        """Insert multiple indicator records"""
        query = """
            INSERT OR REPLACE INTO indicators
            (stock_id, date, indicator_name, value, metadata)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            count = self.execute_many(query, indicator_list)
            logger.info(f"Inserted {count} indicator records")
            return count
        except Exception as e:
            logger.error(f"Error bulk inserting indicators: {e}")
            return 0

    def get_indicators(self, stock_id: str, indicator_name: str = None,
                      start_date: str = None, end_date: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get indicator values"""
        query = "SELECT * FROM indicators WHERE stock_id = ?"
        params = [stock_id]

        if indicator_name:
            query += " AND indicator_name = ?"
            params.append(indicator_name)

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        rows = self.execute_query(query, tuple(params))
        result = []
        for row in rows:
            data = dict(row)
            if data['metadata']:
                data['metadata'] = json.loads(data['metadata'])
            result.append(data)
        return result

    # Signal operations
    def insert_signal(self, stock_id: str, signal_type: str, signal_name: str,
                     detected_date: str, strength: float, metadata: Dict = None) -> bool:
        """Insert a detected signal"""
        query = """
            INSERT INTO signals
            (stock_id, signal_type, signal_name, detected_date, strength, metadata, is_active)
            VALUES (?, ?, ?, ?, ?, ?, TRUE)
        """
        metadata_json = json.dumps(metadata) if metadata else None

        try:
            self.execute_update(
                query,
                (stock_id, signal_type, signal_name, detected_date, strength, metadata_json)
            )
            logger.debug(f"Inserted signal {signal_name} for {stock_id}")
            return True
        except Exception as e:
            logger.error(f"Error inserting signal: {e}")
            return False

    def get_signals(self, stock_id: str = None, signal_type: str = None,
                   active_only: bool = True, min_strength: float = 0,
                   limit: int = None) -> List[Dict[str, Any]]:
        """Get signals based on criteria"""
        query = "SELECT * FROM signals WHERE 1=1"
        params = []

        if stock_id:
            query += " AND stock_id = ?"
            params.append(stock_id)

        if signal_type:
            query += " AND signal_type = ?"
            params.append(signal_type)

        if active_only:
            query += " AND is_active = TRUE"

        if min_strength > 0:
            query += " AND strength >= ?"
            params.append(min_strength)

        query += " ORDER BY detected_date DESC, strength DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        rows = self.execute_query(query, tuple(params))
        result = []
        for row in rows:
            data = dict(row)
            if data['metadata']:
                data['metadata'] = json.loads(data['metadata'])
            result.append(data)
        return result

    def deactivate_old_signals(self, days: int = 5) -> int:
        """Deactivate signals older than specified days"""
        query = """
            UPDATE signals
            SET is_active = FALSE
            WHERE is_active = TRUE
            AND detected_date < date('now', '-' || ? || ' days')
        """
        try:
            count = self.execute_update(query, (days,))
            logger.info(f"Deactivated {count} old signals")
            return count
        except Exception as e:
            logger.error(f"Error deactivating signals: {e}")
            return 0

    # Utility functions
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        stats = {}

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Count stocks
            cursor.execute("SELECT COUNT(*) FROM stocks WHERE is_active = TRUE")
            stats['active_stocks'] = cursor.fetchone()[0]

            # Count price records
            cursor.execute("SELECT COUNT(*) FROM price_data")
            stats['price_records'] = cursor.fetchone()[0]

            # Count indicators
            cursor.execute("SELECT COUNT(*) FROM indicators")
            stats['indicator_records'] = cursor.fetchone()[0]

            # Count active signals
            cursor.execute("SELECT COUNT(*) FROM signals WHERE is_active = TRUE")
            stats['active_signals'] = cursor.fetchone()[0]

            # Latest price date
            cursor.execute("SELECT MAX(date) FROM price_data")
            stats['latest_price_date'] = cursor.fetchone()[0]

        return stats
