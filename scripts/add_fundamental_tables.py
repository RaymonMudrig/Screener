#!/usr/bin/env python3
"""
Add fundamental data tables to the database

This script creates 5 new tables for fundamental analysis:
1. fundamental_data - Quarterly financial statements
2. fundamental_metrics - Calculated metrics (growth, ratios, etc.)
3. ttm_metrics - Trailing 12 months metrics
4. fundamental_signals - Screening results & scores
5. screening_results - Cached screening outcomes
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def add_fundamental_tables(db_path: str = None):
    """Add fundamental data tables to the database"""

    if db_path is None:
        config = get_config()
        db_path = config.get('database.path', 'database/stockCode.sqlite')

    logger.info(f"Adding fundamental tables to {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Table 1: Fundamental Data (Quarterly Reports)
        logger.info("Creating fundamental_data table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundamental_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                year INTEGER NOT NULL,
                quarter INTEGER NOT NULL,
                report_date DATE NOT NULL,
                fiscal_year TEXT,
                month_cover INTEGER,

                -- Stock Info
                close_price REAL,
                par_value REAL,
                shares_outstanding REAL,
                authorized_shares REAL,

                -- Balance Sheet - Assets
                receivables REAL,
                inventories REAL,
                current_assets REAL,
                fixed_assets REAL,
                other_assets REAL,
                total_assets REAL,
                non_current_assets REAL,

                -- Balance Sheet - Liabilities
                current_liabilities REAL,
                long_term_liabilities REAL,
                total_liabilities REAL,

                -- Balance Sheet - Equity
                paidup_capital REAL,
                retained_earnings REAL,
                total_equity REAL,
                minority_interest REAL,

                -- Income Statement
                revenue REAL,
                cost_of_goods_sold REAL,
                gross_profit REAL,
                operating_profit REAL,
                other_income REAL,
                earnings_before_tax REAL,
                tax REAL,
                net_income REAL,

                -- Cash Flow
                cf_operating REAL,
                cf_investing REAL,
                cf_financing REAL,
                net_cash_increase REAL,
                cash_begin REAL,
                cash_end REAL,
                cash_equivalent REAL,

                -- Pre-calculated Ratios
                eps REAL,
                book_value REAL,
                pe_ratio REAL,
                pb_ratio REAL,
                debt_equity_ratio REAL,
                roa_percent REAL,
                roe_percent REAL,
                npm_percent REAL,
                opm_percent REAL,
                gross_margin_percent REAL,
                asset_turnover REAL,

                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(stock_id, year, quarter),
                FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
            )
        """)

        # Table 2: Fundamental Metrics (Calculated)
        logger.info("Creating fundamental_metrics table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundamental_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                year INTEGER NOT NULL,
                quarter INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL,
                metadata TEXT,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(stock_id, year, quarter, metric_name),
                FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
            )
        """)

        # Table 3: TTM Metrics
        logger.info("Creating ttm_metrics table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ttm_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                as_of_date DATE NOT NULL,

                -- TTM Income Statement
                ttm_revenue REAL,
                ttm_gross_profit REAL,
                ttm_operating_profit REAL,
                ttm_net_income REAL,
                ttm_eps REAL,

                -- TTM Margins
                ttm_gross_margin REAL,
                ttm_operating_margin REAL,
                ttm_net_margin REAL,

                -- TTM Cash Flow
                ttm_cf_operating REAL,
                ttm_cf_investing REAL,
                ttm_cf_financing REAL,

                -- TTM Ratios
                ttm_roe REAL,
                ttm_roa REAL,
                ttm_roic REAL,

                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(stock_id, as_of_date),
                FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
            )
        """)

        # Table 4: Fundamental Signals
        logger.info("Creating fundamental_signals table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundamental_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                signal_name TEXT NOT NULL,
                detected_date DATE NOT NULL,
                score REAL,
                details TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
            )
        """)

        # Table 5: Screening Results Cache
        logger.info("Creating screening_results table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screen_name TEXT NOT NULL,
                stock_id TEXT NOT NULL,
                rank INTEGER,
                score REAL,
                criteria_met TEXT,
                screened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
            )
        """)

        # Create Indexes
        logger.info("Creating indexes...")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fundamental_data_stock
            ON fundamental_data(stock_id, year, quarter)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fundamental_data_date
            ON fundamental_data(report_date DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fundamental_metrics_stock
            ON fundamental_metrics(stock_id, metric_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ttm_metrics_stock
            ON ttm_metrics(stock_id, as_of_date DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fundamental_signals_stock
            ON fundamental_signals(stock_id, signal_type, is_active)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fundamental_signals_type
            ON fundamental_signals(signal_type, is_active, score DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_screening_results_screen
            ON screening_results(screen_name, rank)
        """)

        conn.commit()
        logger.info("✓ All fundamental tables created successfully!")

        # Show table counts
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        logger.info(f"Total tables in database: {table_count}")

        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating tables: {e}")
        raise

    finally:
        conn.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Add fundamental data tables')
    parser.add_argument('--db-path', help='Database file path')

    args = parser.parse_args()

    try:
        add_fundamental_tables(args.db_path)
        print("\n✓ Fundamental tables added successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
