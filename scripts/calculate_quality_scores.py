"""
Calculate Quality Scores (Piotroski F-Score and Altman Z-Score)

This script calculates and populates quality metrics:
- piotroski_score: Piotroski F-Score (0-9 scale)
- altman_z_score: Altman Z-Score (bankruptcy prediction)

Author: Claude Code
Date: 2025-11-03
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / 'database' / 'stockCode.sqlite'


def calculate_piotroski_score(data):
    """
    Calculate Piotroski F-Score (0-9 points).
    Simplified version using available data.
    """
    score = 0

    # Profitability (4 points)
    if data.get('net_income') and data['net_income'] > 0:
        score += 1  # Positive net income

    if data.get('cf_operating') and data['cf_operating'] > 0:
        score += 1  # Positive operating cash flow

    if data.get('roa_percent') and data['roa_percent'] > 0:
        score += 1  # Positive ROA

    if data.get('cf_operating') and data.get('net_income'):
        if data['cf_operating'] > data['net_income']:
            score += 1  # Operating CF > Net Income (quality of earnings)

    # Leverage (3 points)
    if data.get('debt_equity_ratio') is not None:
        # Lower debt is better (simplified check)
        if data['debt_equity_ratio'] < 0.5:
            score += 1

    if data.get('current_ratio') and data['current_ratio'] > 1.5:
        score += 1  # Strong liquidity

    # Operating Efficiency (2 points) - simplified
    if data.get('npm_percent') and data['npm_percent'] > 5:
        score += 1  # Decent profit margin

    if data.get('roe_percent') and data['roe_percent'] > 10:
        score += 1  # Decent ROE

    return score


def calculate_altman_z_score(data):
    """
    Calculate Altman Z-Score.
    Simplified version using available data.

    Interpretation:
    Z > 3.0 = Safe zone
    2.7 < Z < 3.0 = Grey zone
    Z < 2.7 = Distress zone
    """
    try:
        # We need: working capital, retained earnings, EBIT, equity, sales, total assets
        total_assets = data.get('total_assets')
        if not total_assets or total_assets == 0:
            return None

        # Working capital = current assets - current liabilities
        working_capital = (data.get('current_assets', 0) - data.get('current_liabilities', 0))

        # Use net income as proxy for EBIT
        ebit = data.get('net_income', 0)

        # Market value of equity (close_price * shares_outstanding)
        shares = data.get('shares_outstanding', 0)
        price = data.get('close_price', 0)
        market_equity = shares * price if shares and price else data.get('total_equity', 0)

        # Sales/Revenue
        sales = data.get('revenue', 0)

        # Total liabilities
        total_liabilities = data.get('total_liabilities', 0)

        # Altman Z-Score formula (manufacturing firms)
        # Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        x1 = working_capital / total_assets if total_assets else 0
        x2 = data.get('retained_earnings', 0) / total_assets if total_assets else 0
        x3 = ebit / total_assets if total_assets else 0
        x4 = market_equity / total_liabilities if total_liabilities else 0
        x5 = sales / total_assets if total_assets else 0

        z_score = (1.2 * x1) + (1.4 * x2) + (3.3 * x3) + (0.6 * x4) + (1.0 * x5)

        return z_score

    except Exception as e:
        return None


def calculate_quality_scores():
    """Calculate and populate quality scores."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 60)
    print("Calculating Quality Scores")
    print("=" * 60)

    # Get latest fundamental data for each stock
    cursor.execute("""
        SELECT fd.*
        FROM fundamental_data fd
        INNER JOIN (
            SELECT stock_id, MAX(year * 100 + quarter) as max_period
            FROM fundamental_data
            GROUP BY stock_id
        ) latest ON fd.stock_id = latest.stock_id
                 AND (fd.year * 100 + fd.quarter) = latest.max_period
        ORDER BY fd.stock_id
    """)

    stocks = cursor.fetchall()
    total_stocks = len(stocks)

    print(f"\nProcessing {total_stocks} stocks...")

    piotroski_count = 0
    altman_count = 0

    for i, stock in enumerate(stocks, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{total_stocks} stocks...")

        stock_id = stock['stock_id']
        year = stock['year']
        quarter = stock['quarter']

        # Calculate Piotroski F-Score
        piotroski = calculate_piotroski_score(dict(stock))
        if piotroski is not None:
            cursor.execute("""
                INSERT OR REPLACE INTO fundamental_metrics
                (stock_id, year, quarter, metric_name, value)
                VALUES (?, ?, ?, ?, ?)
            """, (stock_id, year, quarter, 'piotroski_score', piotroski))
            piotroski_count += 1

        # Calculate Altman Z-Score
        altman = calculate_altman_z_score(dict(stock))
        if altman is not None:
            cursor.execute("""
                INSERT OR REPLACE INTO fundamental_metrics
                (stock_id, year, quarter, metric_name, value)
                VALUES (?, ?, ?, ?, ?)
            """, (stock_id, year, quarter, 'altman_z_score', altman))
            altman_count += 1

    conn.commit()

    print(f"\n✓ Calculation complete!")
    print(f"  Piotroski scores calculated: {piotroski_count}")
    print(f"  Altman Z-scores calculated: {altman_count}")

    # Show distribution
    print("\n" + "=" * 60)
    print("Score Distribution")
    print("=" * 60)

    cursor.execute("""
        SELECT
            ROUND(value) as score,
            COUNT(*) as count
        FROM fundamental_metrics
        WHERE metric_name = 'piotroski_score'
        GROUP BY ROUND(value)
        ORDER BY score
    """)

    print("\nPiotroski F-Score:")
    for row in cursor.fetchall():
        print(f"  Score {int(row['score'])}: {row['count']} stocks")

    cursor.execute("""
        SELECT
            CASE
                WHEN value >= 3.0 THEN 'Safe (>= 3.0)'
                WHEN value >= 2.7 THEN 'Grey (2.7-3.0)'
                ELSE 'Distress (< 2.7)'
            END as zone,
            COUNT(*) as count
        FROM fundamental_metrics
        WHERE metric_name = 'altman_z_score'
        GROUP BY zone
        ORDER BY zone
    """)

    print("\nAltman Z-Score:")
    for row in cursor.fetchall():
        print(f"  {row['zone']}: {row['count']} stocks")

    conn.close()
    print("\n" + "=" * 60)


if __name__ == '__main__':
    try:
        calculate_quality_scores()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
