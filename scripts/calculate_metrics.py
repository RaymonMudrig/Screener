"""
Calculate Derived Fundamental Metrics

This script calculates and populates the fundamental_metrics table with:
- market_cap: Market capitalization (close_price * shares_outstanding)
- revenue_growth_yoy: Year-over-year revenue growth percentage
- eps_growth_yoy: Year-over-year EPS growth percentage

Author: Claude Code
Date: 2025-11-03
"""

import sqlite3
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / 'database' / 'stockCode.sqlite'


def calculate_metrics():
    """Calculate and populate fundamental metrics."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 60)
    print("Calculating Fundamental Metrics")
    print("=" * 60)

    # Get all stock IDs
    cursor.execute("SELECT DISTINCT stock_id FROM fundamental_data ORDER BY stock_id")
    stocks = [row['stock_id'] for row in cursor.fetchall()]

    total_stocks = len(stocks)
    print(f"\nProcessing {total_stocks} stocks...")

    metrics_inserted = 0
    stocks_processed = 0

    for stock_id in stocks:
        stocks_processed += 1
        if stocks_processed % 50 == 0:
            print(f"  Processed {stocks_processed}/{total_stocks} stocks...")

        # Get all quarters for this stock, ordered by date
        cursor.execute("""
            SELECT
                id, stock_id, year, quarter,
                revenue, eps, close_price, shares_outstanding,
                report_date, current_assets, current_liabilities,
                total_liabilities, total_assets
            FROM fundamental_data
            WHERE stock_id = ?
            ORDER BY year, quarter
        """, (stock_id,))

        quarters = cursor.fetchall()

        for i, current in enumerate(quarters):
            year = current['year']
            quarter = current['quarter']

            # 1. Calculate Market Cap
            if current['close_price'] and current['shares_outstanding']:
                market_cap = current['close_price'] * current['shares_outstanding']

                cursor.execute("""
                    INSERT OR REPLACE INTO fundamental_metrics
                    (stock_id, year, quarter, metric_name, value, calculated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (stock_id, year, quarter, 'market_cap', market_cap, datetime.now()))
                metrics_inserted += 1

            # 2. Calculate YoY Revenue Growth
            # Find same quarter from previous year
            prev_year = year - 1
            prev_quarter = next((q for q in quarters
                               if q['year'] == prev_year and q['quarter'] == quarter), None)

            if prev_quarter and current['revenue'] and prev_quarter['revenue']:
                if prev_quarter['revenue'] != 0:
                    revenue_growth = ((current['revenue'] - prev_quarter['revenue']) /
                                    prev_quarter['revenue']) * 100

                    cursor.execute("""
                        INSERT OR REPLACE INTO fundamental_metrics
                        (stock_id, year, quarter, metric_name, value, calculated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (stock_id, year, quarter, 'revenue_growth_yoy', revenue_growth, datetime.now()))
                    metrics_inserted += 1

            # 3. Calculate YoY EPS Growth
            if prev_quarter and current['eps'] and prev_quarter['eps']:
                if prev_quarter['eps'] != 0:
                    eps_growth = ((current['eps'] - prev_quarter['eps']) /
                                prev_quarter['eps']) * 100

                    cursor.execute("""
                        INSERT OR REPLACE INTO fundamental_metrics
                        (stock_id, year, quarter, metric_name, value, calculated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (stock_id, year, quarter, 'eps_growth_yoy', eps_growth, datetime.now()))
                    metrics_inserted += 1

            # 4. Calculate Current Ratio
            if current['current_assets'] and current['current_liabilities']:
                if current['current_liabilities'] != 0:
                    current_ratio = current['current_assets'] / current['current_liabilities']

                    cursor.execute("""
                        INSERT OR REPLACE INTO fundamental_metrics
                        (stock_id, year, quarter, metric_name, value, calculated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (stock_id, year, quarter, 'current_ratio', current_ratio, datetime.now()))
                    metrics_inserted += 1

            # 5. Calculate Debt to Assets Ratio
            if current['total_liabilities'] is not None and current['total_assets']:
                if current['total_assets'] != 0:
                    debt_to_assets = current['total_liabilities'] / current['total_assets']

                    cursor.execute("""
                        INSERT OR REPLACE INTO fundamental_metrics
                        (stock_id, year, quarter, metric_name, value, calculated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (stock_id, year, quarter, 'debt_to_assets', debt_to_assets, datetime.now()))
                    metrics_inserted += 1

    conn.commit()

    print(f"\n✓ Calculation complete!")
    print(f"  Stocks processed: {stocks_processed}")
    print(f"  Metrics inserted: {metrics_inserted}")

    # Show summary statistics
    print("\n" + "=" * 60)
    print("Metrics Summary")
    print("=" * 60)

    cursor.execute("""
        SELECT
            metric_name,
            COUNT(*) as count,
            ROUND(AVG(value), 2) as avg_value,
            ROUND(MIN(value), 2) as min_value,
            ROUND(MAX(value), 2) as max_value
        FROM fundamental_metrics
        WHERE metric_name IN ('market_cap', 'revenue_growth_yoy', 'eps_growth_yoy')
        GROUP BY metric_name
        ORDER BY metric_name
    """)

    for row in cursor.fetchall():
        print(f"\n{row['metric_name']}:")
        print(f"  Count: {row['count']}")
        print(f"  Average: {row['avg_value']}")
        print(f"  Min: {row['min_value']}")
        print(f"  Max: {row['max_value']}")

    conn.close()
    print("\n" + "=" * 60)


if __name__ == '__main__':
    try:
        calculate_metrics()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
