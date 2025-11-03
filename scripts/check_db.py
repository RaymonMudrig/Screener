#!/usr/bin/env python3
"""
Check if database is initialized
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import get_config

def check_database():
    """Check if database exists and has required tables"""
    config = get_config()
    db_path = config.get('database.path', 'database/stockCode.sqlite')

    db_file = Path(db_path)

    print(f"Checking database at: {db_path}\n")

    if not db_file.exists():
        print("✗ Database file does not exist")
        print("\nRun this command to create it:")
        print("  python3 -m src.api.cli init")
        return False

    print("✓ Database file exists")

    # Check for required tables
    required_tables = ['stocks', 'price_data', 'indicators', 'signals']

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        print(f"✓ Found {len(existing_tables)} tables\n")

        missing_tables = []
        for table in required_tables:
            if table in existing_tables:
                # Count records
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✓ {table:15s} - {count:,} records")
            else:
                print(f"  ✗ {table:15s} - MISSING")
                missing_tables.append(table)

        conn.close()

        if missing_tables:
            print(f"\n✗ Missing tables: {', '.join(missing_tables)}")
            print("\nRun this command to initialize:")
            print("  python3 -m src.api.cli init --reset")
            return False

        print("\n✓ Database is properly initialized!")
        return True

    except Exception as e:
        print(f"\n✗ Error checking database: {e}")
        return False

if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)
