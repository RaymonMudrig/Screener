#!/usr/bin/env python3
"""
Create Pattern Tables

Adds database tables for the pattern-based screening system.
This enables users to create, save, and manage screening patterns
that combine technical and fundamental criteria.

Tables:
- screening_patterns: Stores pattern definitions
- pattern_results_cache: Caches screening results for performance

Usage:
    python3 scripts/create_pattern_tables.py [--db-path PATH]
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_pattern_tables(db_path: str = 'database/stockCode.sqlite') -> None:
    """
    Create pattern system tables in the database.

    Args:
        db_path: Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Creating pattern system tables...")

    # Table 1: screening_patterns
    # Stores pattern definitions (both preset and custom)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_patterns (
            pattern_id TEXT PRIMARY KEY,
            pattern_name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            technical_criteria TEXT,  -- JSON: {signals: [...], min_signal_strength: ...}
            fundamental_criteria TEXT, -- JSON: {pe_ratio: {min:, max:}, ...}
            sort_by TEXT,
            created_by TEXT DEFAULT 'system',
            is_preset BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created screening_patterns table")

    # Table 2: pattern_results_cache
    # Caches screening results for performance
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pattern_results_cache (
            pattern_id TEXT NOT NULL,
            stock_id TEXT NOT NULL,
            match_score INTEGER,
            matched_signals TEXT,  -- JSON: ["Golden Cross", "RSI Oversold"]
            matched_fundamentals TEXT,  -- JSON: {pe_ratio: 12.5, roe_percent: 21.3}
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (pattern_id, stock_id),
            FOREIGN KEY (pattern_id) REFERENCES screening_patterns(pattern_id) ON DELETE CASCADE,
            FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
        )
    """)
    print("✓ Created pattern_results_cache table")

    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_patterns_category
        ON screening_patterns(category)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_patterns_preset
        ON screening_patterns(is_preset)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cache_pattern
        ON pattern_results_cache(pattern_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cache_score
        ON pattern_results_cache(match_score DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cache_updated
        ON pattern_results_cache(last_updated)
    """)

    print("✓ Created 5 indexes for pattern tables")

    conn.commit()
    conn.close()

    print(f"\n✓ Pattern tables created successfully in: {db_path}")


def insert_preset_patterns(db_path: str = 'database/stockCode.sqlite') -> None:
    """
    Insert 10 preset patterns into the database.

    Args:
        db_path: Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\nInserting preset patterns...")

    # Preset Pattern 1: Cheap Quality on Reversal
    cursor.execute("""
        INSERT OR REPLACE INTO screening_patterns
        (pattern_id, pattern_name, description, category, technical_criteria,
         fundamental_criteria, sort_by, is_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'cheap_quality_reversal',
        'Cheap Quality on Reversal',
        'Undervalued quality companies showing technical reversal signals',
        'value',
        json.dumps({
            'signals': ['golden_cross', 'rsi_oversold', 'bullish_macd'],
            'min_signal_strength': 70
        }),
        json.dumps({
            'pe_ratio': {'min': 0, 'max': 15},
            'roe_percent': {'min': 15, 'max': 999},
            'debt_to_assets': {'min': 0, 'max': 0.4}
        }),
        'signal_strength',
        1
    ))
    print("✓ Inserted: Cheap Quality on Reversal")

    # Preset Pattern 2: High Growth Momentum
    cursor.execute("""
        INSERT OR REPLACE INTO screening_patterns
        (pattern_id, pattern_name, description, category, technical_criteria,
         fundamental_criteria, sort_by, is_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'high_growth_momentum',
        'High Growth Momentum',
        'Fast-growing companies with strong technical momentum',
        'growth',
        json.dumps({
            'signals': ['bullish_trend', 'rsi_bullish', 'macd_positive'],
            'min_signal_strength': 75
        }),
        json.dumps({
            'revenue_growth_yoy': {'min': 20, 'max': 999},
            'eps_growth_yoy': {'min': 15, 'max': 999},
            'roe_percent': {'min': 12, 'max': 999}
        }),
        'revenue_growth_yoy',
        1
    ))
    print("✓ Inserted: High Growth Momentum")

    # Preset Pattern 3: GARP (Growth at Reasonable Price)
    cursor.execute("""
        INSERT OR REPLACE INTO screening_patterns
        (pattern_id, pattern_name, description, category, technical_criteria,
         fundamental_criteria, sort_by, is_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'garp',
        'GARP - Growth at Reasonable Price',
        'Growth stocks trading at reasonable valuations',
        'growth',
        json.dumps({}),  # No technical criteria
        json.dumps({
            'peg_ratio': {'min': 0, 'max': 1.0},
            'eps_growth_yoy': {'min': 10, 'max': 999},
            'roe_percent': {'min': 12, 'max': 999},
            'pe_ratio': {'min': 0, 'max': 25}
        }),
        'peg_ratio',
        1
    ))
    print("✓ Inserted: GARP - Growth at Reasonable Price")

    # Preset Pattern 4: Magic Formula
    cursor.execute("""
        INSERT OR REPLACE INTO screening_patterns
        (pattern_id, pattern_name, description, category, technical_criteria,
         fundamental_criteria, sort_by, is_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'magic_formula',
        'Magic Formula',
        'High-quality businesses at reasonable prices (Greenblatt)',
        'quality',
        json.dumps({}),  # No technical criteria
        json.dumps({
            'roic': {'min': 12, 'max': 999},
            'ev_ebitda': {'min': 0, 'max': 15}
        }),
        'roic',
        1
    ))
    print("✓ Inserted: Magic Formula")

    # Preset Pattern 5: Oversold Bounce
    cursor.execute("""
        INSERT OR REPLACE INTO screening_patterns
        (pattern_id, pattern_name, description, category, technical_criteria,
         fundamental_criteria, sort_by, is_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'oversold_bounce',
        'Oversold Bounce',
        'Quality stocks showing oversold technical conditions',
        'technical',
        json.dumps({
            'signals': ['rsi_oversold', 'stochastic_oversold'],
            'min_signal_strength': 70
        }),
        json.dumps({
            'roe_percent': {'min': 10, 'max': 999}  # Ensure quality
        }),
        'signal_strength',
        1
    ))
    print("✓ Inserted: Oversold Bounce")

    # Preset Pattern 6: Blue Chip Quality
    cursor.execute("""
        INSERT OR REPLACE INTO screening_patterns
        (pattern_id, pattern_name, description, category, technical_criteria,
         fundamental_criteria, sort_by, is_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'blue_chip_quality',
        'Blue Chip Quality',
        'Large, financially strong, high-quality companies',
        'quality',
        json.dumps({}),  # No technical criteria
        json.dumps({
            'piotroski_score': {'min': 7, 'max': 9},
            'roe_percent': {'min': 15, 'max': 999},
            'current_ratio': {'min': 2.0, 'max': 999},
            'debt_to_assets': {'min': 0, 'max': 0.5},
            'market_cap': {'min': 10000000000, 'max': None}  # 10B minimum
        }),
        'piotroski_score',
        1
    ))
    print("✓ Inserted: Blue Chip Quality")

    # Preset Pattern 7: Deep Value
    cursor.execute("""
        INSERT OR REPLACE INTO screening_patterns
        (pattern_id, pattern_name, description, category, technical_criteria,
         fundamental_criteria, sort_by, is_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'deep_value',
        'Deep Value',
        'Stocks trading below book value with profitability',
        'value',
        json.dumps({}),  # No technical criteria
        json.dumps({
            'pb_ratio': {'min': 0, 'max': 1.0},  # Below book value
            'pe_ratio': {'min': 0, 'max': 10},
            'roe_percent': {'min': 5, 'max': 999}  # Some profitability
        }),
        'pb_ratio',
        1
    ))
    print("✓ Inserted: Deep Value")

    # Preset Pattern 8: Financial Fortress
    cursor.execute("""
        INSERT OR REPLACE INTO screening_patterns
        (pattern_id, pattern_name, description, category, technical_criteria,
         fundamental_criteria, sort_by, is_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'financial_fortress',
        'Financial Fortress',
        'Companies with exceptional financial strength and health',
        'health',
        json.dumps({}),  # No technical criteria
        json.dumps({
            'piotroski_score': {'min': 7, 'max': 9},
            'current_ratio': {'min': 2.0, 'max': 999},
            'debt_to_assets': {'min': 0, 'max': 0.3},
            'altman_z_score': {'min': 3.0, 'max': 999},
            'cf_operating': {'min': 0, 'max': None}
        }),
        'piotroski_score',
        1
    ))
    print("✓ Inserted: Financial Fortress")

    # Preset Pattern 9: Small Cap Growth
    cursor.execute("""
        INSERT OR REPLACE INTO screening_patterns
        (pattern_id, pattern_name, description, category, technical_criteria,
         fundamental_criteria, sort_by, is_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'small_cap_growth',
        'Small Cap Growth',
        'Small-cap companies with high growth rates',
        'growth',
        json.dumps({}),  # No technical criteria
        json.dumps({
            'market_cap': {'min': 500000000, 'max': 5000000000},  # 500M - 5B
            'revenue_growth_yoy': {'min': 25, 'max': 999},
            'eps_growth_yoy': {'min': 20, 'max': 999},
            'roe_percent': {'min': 15, 'max': 999}
        }),
        'revenue_growth_yoy',
        1
    ))
    print("✓ Inserted: Small Cap Growth")

    # Preset Pattern 10: Breakout with Volume
    cursor.execute("""
        INSERT OR REPLACE INTO screening_patterns
        (pattern_id, pattern_name, description, category, technical_criteria,
         fundamental_criteria, sort_by, is_preset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'breakout_volume',
        'Breakout with Volume',
        'Technical breakouts confirmed by high volume',
        'technical',
        json.dumps({
            'signals': ['bullish_breakout', 'volume_surge', 'rsi_bullish'],
            'min_signal_strength': 75
        }),
        json.dumps({
            'market_cap': {'min': 1000000000, 'max': None}  # 1B minimum
        }),
        'signal_strength',
        1
    ))
    print("✓ Inserted: Breakout with Volume")

    conn.commit()
    conn.close()

    print(f"\n✓ Successfully inserted 10 preset patterns into: {db_path}")


def verify_pattern_tables(db_path: str = 'database/stockCode.sqlite') -> None:
    """
    Verify that pattern tables were created correctly.

    Args:
        db_path: Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\nVerifying pattern tables...")

    # Check screening_patterns table
    cursor.execute("SELECT COUNT(*) FROM screening_patterns WHERE is_preset = 1")
    preset_count = cursor.fetchone()[0]
    print(f"✓ Found {preset_count} preset patterns")

    # List all preset patterns
    cursor.execute("""
        SELECT pattern_id, pattern_name, category
        FROM screening_patterns
        WHERE is_preset = 1
        ORDER BY category, pattern_name
    """)
    patterns = cursor.fetchall()

    print("\nPreset Patterns:")
    print("-" * 80)
    categories = {}
    for pattern_id, pattern_name, category in patterns:
        if category not in categories:
            categories[category] = []
        categories[category].append((pattern_id, pattern_name))

    for category in sorted(categories.keys()):
        print(f"\n{category.upper()}:")
        for pattern_id, pattern_name in categories[category]:
            print(f"  • {pattern_name} ({pattern_id})")

    # Check indexes
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='index' AND (name LIKE 'idx_patterns_%' OR name LIKE 'idx_cache_%')
    """)
    indexes = [row[0] for row in cursor.fetchall()]
    print(f"\n✓ Found {len(indexes)} pattern-related indexes")

    conn.close()
    print("\n✓ Pattern tables verified successfully")


def main():
    """Main function to create pattern tables and insert presets."""
    import argparse

    parser = argparse.ArgumentParser(description='Create pattern system tables')
    parser.add_argument('--db-path', default='database/stockCode.sqlite',
                       help='Path to SQLite database')
    args = parser.parse_args()

    print("=" * 80)
    print("PATTERN SYSTEM SETUP")
    print("=" * 80)

    # Create tables
    create_pattern_tables(args.db_path)

    # Insert preset patterns
    insert_preset_patterns(args.db_path)

    # Verify
    verify_pattern_tables(args.db_path)

    print("\n" + "=" * 80)
    print("PATTERN SYSTEM READY")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Use CLI: python3 -m src.api.cli list-patterns")
    print("2. Run pattern: python3 -m src.api.cli run-pattern cheap_quality_reversal")
    print("3. Create custom pattern via API or CLI")


if __name__ == '__main__':
    main()
