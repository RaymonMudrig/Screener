"""
Pattern Storage Module

Handles CRUD operations for screening patterns in the database.
Manages both preset and custom user-created patterns.

Author: Claude Code
Date: 2025-11-03
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime


class PatternStorage:
    """Manages storage and retrieval of screening patterns."""

    def __init__(self, db_path: str = 'database/stockCode.sqlite'):
        """
        Initialize pattern storage.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_patterns(self, include_custom: bool = True) -> List[Dict[str, Any]]:
        """
        Get all patterns from database.

        Args:
            include_custom: Include custom patterns (default True)

        Returns:
            List of pattern dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if include_custom:
            query = """
                SELECT * FROM screening_patterns
                ORDER BY is_preset DESC, category, pattern_name
            """
            cursor.execute(query)
        else:
            query = """
                SELECT * FROM screening_patterns
                WHERE is_preset = 1
                ORDER BY category, pattern_name
            """
            cursor.execute(query)

        patterns = []
        for row in cursor.fetchall():
            pattern = dict(row)
            # Parse JSON fields
            if pattern['technical_criteria']:
                pattern['technical_criteria'] = json.loads(pattern['technical_criteria'])
            if pattern['fundamental_criteria']:
                pattern['fundamental_criteria'] = json.loads(pattern['fundamental_criteria'])
            patterns.append(pattern)

        conn.close()
        return patterns

    def get_preset_patterns(self) -> List[Dict[str, Any]]:
        """
        Get only preset patterns.

        Returns:
            List of preset pattern dictionaries
        """
        return self.get_all_patterns(include_custom=False)

    def get_custom_patterns(self) -> List[Dict[str, Any]]:
        """
        Get only custom user-created patterns.

        Returns:
            List of custom pattern dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM screening_patterns
            WHERE is_preset = 0
            ORDER BY updated_at DESC
        """
        cursor.execute(query)

        patterns = []
        for row in cursor.fetchall():
            pattern = dict(row)
            # Parse JSON fields
            if pattern['technical_criteria']:
                pattern['technical_criteria'] = json.loads(pattern['technical_criteria'])
            if pattern['fundamental_criteria']:
                pattern['fundamental_criteria'] = json.loads(pattern['fundamental_criteria'])
            patterns.append(pattern)

        conn.close()
        return patterns

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern dictionary or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM screening_patterns WHERE pattern_id = ?"
        cursor.execute(query, (pattern_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        pattern = dict(row)
        # Parse JSON fields
        if pattern['technical_criteria']:
            pattern['technical_criteria'] = json.loads(pattern['technical_criteria'])
        else:
            pattern['technical_criteria'] = {}

        if pattern['fundamental_criteria']:
            pattern['fundamental_criteria'] = json.loads(pattern['fundamental_criteria'])
        else:
            pattern['fundamental_criteria'] = {}

        return pattern

    def get_patterns_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get patterns by category.

        Args:
            category: Category name (value, growth, quality, health, technical, composite)

        Returns:
            List of pattern dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM screening_patterns
            WHERE category = ?
            ORDER BY is_preset DESC, pattern_name
        """
        cursor.execute(query, (category,))

        patterns = []
        for row in cursor.fetchall():
            pattern = dict(row)
            # Parse JSON fields
            if pattern['technical_criteria']:
                pattern['technical_criteria'] = json.loads(pattern['technical_criteria'])
            if pattern['fundamental_criteria']:
                pattern['fundamental_criteria'] = json.loads(pattern['fundamental_criteria'])
            patterns.append(pattern)

        conn.close()
        return patterns

    def create_pattern(self, pattern_data: Dict[str, Any]) -> bool:
        """
        Create a new custom pattern.

        Args:
            pattern_data: Pattern definition with required fields:
                - pattern_id: Unique identifier
                - pattern_name: Display name
                - category: Category name
                - technical_criteria: Dict of technical criteria (optional)
                - fundamental_criteria: Dict of fundamental criteria (optional)
                - description: Pattern description (optional)
                - sort_by: Sort field for results (optional)

        Returns:
            True if successful, False otherwise
        """
        required_fields = ['pattern_id', 'pattern_name', 'category']
        for field in required_fields:
            if field not in pattern_data:
                raise ValueError(f"Missing required field: {field}")

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO screening_patterns
                (pattern_id, pattern_name, description, category,
                 technical_criteria, fundamental_criteria, sort_by,
                 created_by, is_preset, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern_data['pattern_id'],
                pattern_data['pattern_name'],
                pattern_data.get('description', ''),
                pattern_data['category'],
                json.dumps(pattern_data.get('technical_criteria', {})),
                json.dumps(pattern_data.get('fundamental_criteria', {})),
                pattern_data.get('sort_by', 'match_score'),
                pattern_data.get('created_by', 'user'),
                0,  # is_preset = False for custom patterns
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            # Clear cache for this pattern since it's new
            self.clear_pattern_cache(pattern_data['pattern_id'])

            return True

        except sqlite3.IntegrityError as e:
            conn.close()
            raise ValueError(f"Pattern ID already exists: {pattern_data['pattern_id']}")

        except Exception as e:
            conn.close()
            raise Exception(f"Failed to create pattern: {str(e)}")

    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing pattern.

        Args:
            pattern_id: Pattern identifier
            updates: Dictionary of fields to update

        Returns:
            True if successful, False if pattern not found
        """
        # Check if pattern exists and is not preset
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return False

        if pattern['is_preset']:
            raise ValueError("Cannot modify preset patterns")

        conn = self._get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        update_fields = []
        update_values = []

        allowed_fields = ['pattern_name', 'description', 'category',
                         'technical_criteria', 'fundamental_criteria', 'sort_by']

        for field in allowed_fields:
            if field in updates:
                update_fields.append(f"{field} = ?")
                # JSON encode criteria fields
                if field in ['technical_criteria', 'fundamental_criteria']:
                    update_values.append(json.dumps(updates[field]))
                else:
                    update_values.append(updates[field])

        if not update_fields:
            conn.close()
            return False

        # Add updated_at timestamp
        update_fields.append("updated_at = ?")
        update_values.append(datetime.now().isoformat())

        # Add pattern_id for WHERE clause
        update_values.append(pattern_id)

        query = f"""
            UPDATE screening_patterns
            SET {', '.join(update_fields)}
            WHERE pattern_id = ?
        """

        cursor.execute(query, tuple(update_values))
        conn.commit()
        conn.close()

        # Clear cache for this pattern since it was modified
        self.clear_pattern_cache(pattern_id)

        return True

    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Delete a custom pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            True if successful, False if pattern not found
        """
        # Check if pattern exists and is not preset
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return False

        if pattern['is_preset']:
            raise ValueError("Cannot delete preset patterns")

        conn = self._get_connection()
        cursor = conn.cursor()

        # Delete pattern (cascade will delete cached results)
        cursor.execute("DELETE FROM screening_patterns WHERE pattern_id = ?", (pattern_id,))

        conn.commit()
        conn.close()

        return True

    def save_pattern_results(self, pattern_id: str, results: List[Dict[str, Any]]) -> None:
        """
        Cache pattern screening results.

        Args:
            pattern_id: Pattern identifier
            results: List of matching stocks with scores
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Clear old results for this pattern
        cursor.execute("DELETE FROM pattern_results_cache WHERE pattern_id = ?", (pattern_id,))

        # Insert new results
        for result in results:
            cursor.execute("""
                INSERT INTO pattern_results_cache
                (pattern_id, stock_id, match_score, matched_signals,
                 matched_fundamentals, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pattern_id,
                result['stock_id'],
                result.get('match_score', 0),
                json.dumps(result.get('matched_signals', [])),
                json.dumps(result.get('matched_fundamentals', {})),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

    def get_pattern_results(self, pattern_id: str,
                          max_age_hours: int = 24) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached pattern results.

        Args:
            pattern_id: Pattern identifier
            max_age_hours: Maximum age of cache in hours (default 24)

        Returns:
            List of cached results or None if cache is stale/empty
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM pattern_results_cache
            WHERE pattern_id = ?
            AND datetime(last_updated) > datetime('now', '-' || ? || ' hours')
            ORDER BY match_score DESC
        """

        cursor.execute(query, (pattern_id, max_age_hours))

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            # Parse JSON fields
            result['matched_signals'] = json.loads(result['matched_signals'])
            result['matched_fundamentals'] = json.loads(result['matched_fundamentals'])
            results.append(result)

        conn.close()

        return results if results else None

    def clear_pattern_cache(self, pattern_id: Optional[str] = None) -> int:
        """
        Clear cached pattern results.

        Args:
            pattern_id: Specific pattern to clear, or None to clear all

        Returns:
            Number of cache entries deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if pattern_id:
            cursor.execute("DELETE FROM pattern_results_cache WHERE pattern_id = ?", (pattern_id,))
        else:
            cursor.execute("DELETE FROM pattern_results_cache")

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    def get_pattern_count(self) -> Dict[str, int]:
        """
        Get count of patterns by type.

        Returns:
            Dictionary with preset and custom counts
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM screening_patterns WHERE is_preset = 1")
        preset_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM screening_patterns WHERE is_preset = 0")
        custom_count = cursor.fetchone()[0]

        conn.close()

        return {
            'preset': preset_count,
            'custom': custom_count,
            'total': preset_count + custom_count
        }
