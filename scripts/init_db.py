"""
Database initialization script
Creates the stock screener database schema
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.logger import get_logger

logger = get_logger(__name__)


def init_database(db_path: str = "database/stockCode.sqlite") -> None:
    """Initialize the database with schema"""

    # Ensure database directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing database at {db_path}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create stocks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                stock_id TEXT PRIMARY KEY,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                sector TEXT,
                subsector TEXT,
                last_updated TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        logger.info("Created stocks table")

        # Create price_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
                UNIQUE(stock_id, date)
            )
        """)
        logger.info("Created price_data table")

        # Create indicators table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                date DATE NOT NULL,
                indicator_name TEXT NOT NULL,
                value REAL,
                metadata TEXT,
                FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
                UNIQUE(stock_id, date, indicator_name)
            )
        """)
        logger.info("Created indicators table")

        # Create signals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                signal_name TEXT NOT NULL,
                detected_date DATE NOT NULL,
                strength REAL,
                metadata TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
            )
        """)
        logger.info("Created signals table")

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_price_stock_date
            ON price_data(stock_id, date DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_indicators_stock_date
            ON indicators(stock_id, date DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_date
            ON signals(detected_date DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_active
            ON signals(is_active, signal_type)
        """)
        logger.info("Created indexes")

        # Commit changes
        conn.commit()
        logger.info("Database initialization completed successfully")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error initializing database: {e}")
        raise

    finally:
        conn.close()


def drop_all_tables(db_path: str = "database/stockCode.sqlite") -> None:
    """Drop all tables (use with caution!)"""
    logger.warning(f"Dropping all tables in {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DROP TABLE IF EXISTS signals")
        cursor.execute("DROP TABLE IF EXISTS indicators")
        cursor.execute("DROP TABLE IF EXISTS price_data")
        cursor.execute("DROP TABLE IF EXISTS stocks")

        conn.commit()
        logger.info("All tables dropped")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error dropping tables: {e}")
        raise

    finally:
        conn.close()


def reset_database(db_path: str = "database/stockCode.sqlite") -> None:
    """Drop and recreate all tables"""
    drop_all_tables(db_path)
    init_database(db_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize stock screener database")
    parser.add_argument(
        "--db-path",
        default="database/stockCode.sqlite",
        help="Path to database file"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drop and recreate all tables)"
    )

    args = parser.parse_args()

    if args.reset:
        confirm = input("Are you sure you want to reset the database? All data will be lost! (yes/no): ")
        if confirm.lower() == "yes":
            reset_database(args.db_path)
        else:
            logger.info("Reset cancelled")
    else:
        init_database(args.db_path)
