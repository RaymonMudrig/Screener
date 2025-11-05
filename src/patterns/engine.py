"""
Pattern Engine Module

Executes screening patterns by combining technical and fundamental criteria.
Scores and ranks stocks based on pattern matching.

Author: Claude Code
Date: 2025-11-03
"""

import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.patterns.storage import PatternStorage
from src.fundamentals.screener import FundamentalScreener


class PatternEngine:
    """Executes screening patterns and scores matching stocks."""

    def __init__(self, db_path: str = 'database/stockCode.sqlite'):
        """
        Initialize pattern engine.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.storage = PatternStorage(db_path)
        self.fundamental_screener = FundamentalScreener(db_path)
        self.conn = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def run_pattern(self, pattern_id: str, use_cache: bool = True,
                   cache_max_age_hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Run a screening pattern and return matching stocks.

        Args:
            pattern_id: Pattern identifier
            use_cache: Use cached results if available
            cache_max_age_hours: Maximum age of cache in hours
            limit: Maximum number of results to return

        Returns:
            List of matching stocks with scores and details
        """
        # Check cache first
        if use_cache:
            cached_results = self.storage.get_pattern_results(
                pattern_id, max_age_hours=cache_max_age_hours
            )
            if cached_results:
                return cached_results[:limit]

        # Load pattern
        pattern = self.storage.get_pattern(pattern_id)
        if not pattern:
            raise ValueError(f"Pattern not found: {pattern_id}")

        # Get matching stocks
        results = self._execute_pattern(pattern)

        # Score and sort
        results = self._score_results(results, pattern)

        # Cache results
        self.storage.save_pattern_results(pattern_id, results)

        # Return limited results
        return results[:limit]

    def _execute_pattern(self, pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute pattern screening.

        Args:
            pattern: Pattern definition

        Returns:
            List of matching stocks
        """
        technical_criteria = pattern.get('technical_criteria', {})
        fundamental_criteria = pattern.get('fundamental_criteria', {})

        # Start with all stocks if no criteria, otherwise filter progressively
        if not technical_criteria and not fundamental_criteria:
            return []

        matching_stocks = {}

        # Screen by fundamental criteria
        if fundamental_criteria:
            fundamental_matches = self._screen_fundamentals(fundamental_criteria)
            for stock in fundamental_matches:
                stock_id = stock['stock_id']
                if stock_id not in matching_stocks:
                    matching_stocks[stock_id] = {
                        'stock_id': stock_id,
                        'matched_fundamentals': stock,
                        'matched_signals': [],
                        'fundamental_score': stock.get('score', 0),
                        'technical_score': 0
                    }

        # Screen by technical criteria
        if technical_criteria:
            technical_matches = self._screen_technical(technical_criteria)

            if not fundamental_criteria:
                # Pure technical pattern
                for stock in technical_matches:
                    stock_id = stock['stock_id']
                    matching_stocks[stock_id] = {
                        'stock_id': stock_id,
                        'matched_fundamentals': {},
                        'matched_signals': stock.get('signals', []),
                        'fundamental_score': 0,
                        'technical_score': stock.get('signal_strength', 0)
                    }
            else:
                # Combined pattern - enhance existing matches with technical data
                for stock in technical_matches:
                    stock_id = stock['stock_id']
                    if stock_id in matching_stocks:
                        matching_stocks[stock_id]['matched_signals'] = stock.get('signals', [])
                        matching_stocks[stock_id]['technical_score'] = stock.get('signal_strength', 0)

                # Remove stocks that don't meet technical criteria (if specified)
                if technical_criteria.get('signals'):
                    matching_stocks = {
                        k: v for k, v in matching_stocks.items()
                        if v['technical_score'] > 0
                    }

        return list(matching_stocks.values())

    def _screen_fundamentals(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Screen stocks by fundamental criteria.

        Args:
            criteria: Fundamental criteria from pattern

        Returns:
            List of stocks meeting fundamental criteria
        """
        # Use generic screening that can handle multiple criteria
        return self._generic_fundamental_screen(criteria)

    def _generic_fundamental_screen(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generic fundamental screener that applies all criteria dynamically.

        Args:
            criteria: Dictionary of fundamental metric criteria

        Returns:
            List of stocks meeting all criteria
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build SQL query dynamically
        conditions = []
        params = []
        joins = []

        # Map criteria keys to database columns in fundamental_data
        fundamental_data_columns = {
            'pe_ratio': 'fd.pe_ratio',
            'pb_ratio': 'fd.pb_ratio',
            'roe_percent': 'fd.roe_percent',
            'roa_percent': 'fd.roa_percent',
            'npm_percent': 'fd.npm_percent',
            'debt_to_equity': 'fd.debt_equity_ratio',
            'cf_operating': 'fd.cf_operating',
            'cf_investing': 'fd.cf_investing',
            'cf_financing': 'fd.cf_financing',
        }

        # Metrics that need to be joined from fundamental_metrics table
        metrics_table_columns = [
            'peg_ratio', 'ps_ratio', 'revenue_growth_yoy', 'eps_growth_yoy',
            'roic', 'piotroski_score', 'altman_z_score', 'ev_ebitda',
            'current_ratio', 'quick_ratio', 'debt_to_assets', 'cash_ratio', 'market_cap'
        ]

        # Build WHERE conditions for fundamental_data columns
        for metric, bounds in criteria.items():
            if metric in fundamental_data_columns:
                col = fundamental_data_columns[metric]
                if isinstance(bounds, dict):
                    if 'min' in bounds and bounds['min'] is not None:
                        conditions.append(f"{col} >= ?")
                        params.append(bounds['min'])
                    if 'max' in bounds and bounds['max'] is not None and bounds['max'] != 999 and bounds['max'] != 999999999999:
                        conditions.append(f"{col} <= ?")
                        params.append(bounds['max'])

            elif metric in metrics_table_columns:
                # Add join and condition for fundamental_metrics table
                # Use subquery to get most recent value per stock for the metric
                alias = f"fm_{metric}"
                joins.append(f"""
                    LEFT JOIN (
                        SELECT fm1.stock_id, fm1.value
                        FROM fundamental_metrics fm1
                        INNER JOIN (
                            SELECT stock_id, MAX(year || '-' || quarter) as max_period
                            FROM fundamental_metrics
                            WHERE metric_name = '{metric}'
                            GROUP BY stock_id
                        ) fm2 ON fm1.stock_id = fm2.stock_id
                            AND fm1.year || '-' || fm1.quarter = fm2.max_period
                            AND fm1.metric_name = '{metric}'
                    ) {alias}
                    ON fd.stock_id = {alias}.stock_id
                """)

                if isinstance(bounds, dict):
                    if 'min' in bounds and bounds['min'] is not None:
                        conditions.append(f"{alias}.value >= ?")
                        params.append(bounds['min'])
                    if 'max' in bounds and bounds['max'] is not None and bounds['max'] != 999 and bounds['max'] != 999999999999:
                        conditions.append(f"{alias}.value <= ?")
                        params.append(bounds['max'])

        if not conditions:
            return []

        # Build joins string
        joins_str = ' '.join(joins) if joins else ''

        # Query with all fundamental metrics (using most recent values)
        query = f"""
            SELECT DISTINCT
                fd.stock_id,
                fd.pe_ratio,
                fd.pb_ratio,
                fd.roe_percent,
                fd.roa_percent,
                fd.npm_percent,
                fd.debt_equity_ratio as debt_to_equity,
                fd.cf_operating,
                fd.cf_investing,
                fd.cf_financing,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'peg_ratio' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as peg_ratio,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'ps_ratio' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as ps_ratio,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'revenue_growth_yoy' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as revenue_growth_yoy,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'eps_growth_yoy' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as eps_growth_yoy,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'roic' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as roic,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'piotroski_score' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as piotroski_score,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'altman_z_score' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as altman_z_score,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'ev_ebitda' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as ev_ebitda,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'current_ratio' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as current_ratio,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'quick_ratio' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as quick_ratio,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'debt_to_assets' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as debt_to_assets,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'cash_ratio' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as cash_ratio,
                (SELECT value FROM fundamental_metrics WHERE stock_id = fd.stock_id AND metric_name = 'market_cap' ORDER BY year DESC, quarter DESC, calculated_at DESC LIMIT 1) as market_cap
            FROM fundamental_data fd
            {joins_str}
            WHERE {' AND '.join(conditions)}
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = dict(row)
            result['score'] = 80  # Default score
            results.append(result)

        return results

    def _screen_technical(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Screen stocks by technical criteria.

        Args:
            criteria: Technical criteria from pattern

        Returns:
            List of stocks meeting technical criteria
        """
        required_signals = criteria.get('signals', [])
        min_strength = criteria.get('min_signal_strength', 0)

        if not required_signals:
            return []

        conn = self._get_connection()
        cursor = conn.cursor()

        # Map signal names to database signal types
        signal_mapping = {
            'golden_cross': 'trend',
            'death_cross': 'trend',
            'bullish_macd': 'momentum',
            'bearish_macd': 'momentum',
            'rsi_oversold': 'momentum',
            'rsi_overbought': 'momentum',
            'rsi_bullish': 'momentum',
            'stochastic_oversold': 'momentum',
            'stochastic_overbought': 'momentum',
            'bullish_trend': 'trend',
            'bearish_trend': 'trend',
            'macd_positive': 'momentum',
            'bullish_breakout': 'trend',
            'volume_surge': 'volume',
        }

        # Get stocks with high signal strength
        query = """
            SELECT
                stock_id,
                signal_type,
                signal_name,
                strength
            FROM signals
            WHERE strength >= ?
            AND is_active = 1
            AND detected_date > date('now', '-7 days')
            ORDER BY stock_id, strength DESC
        """

        cursor.execute(query, (min_strength,))

        # Group signals by stock
        stocks_signals = {}
        for row in cursor.fetchall():
            stock_id = row['stock_id']
            if stock_id not in stocks_signals:
                stocks_signals[stock_id] = []

            stocks_signals[stock_id].append({
                'signal_type': row['signal_type'],
                'signal_name': row['signal_name'],
                'strength': row['strength']
            })

        # Filter stocks that have required signals
        results = []
        for stock_id, signals in stocks_signals.items():
            signal_names = [s['signal_name'].lower() for s in signals]

            # Check if stock has any of the required signals
            # Normalize both sides to lowercase for matching
            has_required_signal = any(
                sig.lower() in ' '.join(signal_names)
                for sig in required_signals
            )

            if has_required_signal:
                # Calculate average signal strength
                avg_strength = sum(s['strength'] for s in signals) / len(signals)

                results.append({
                    'stock_id': stock_id,
                    'signals': signals,
                    'signal_strength': int(avg_strength)
                })

        return results

    def _calculate_fundamental_score(self, stock: Dict[str, Any],
                                     criteria: Dict[str, Any]) -> int:
        """
        Calculate fundamental score (0-100) based on criteria match.

        Args:
            stock: Stock data
            criteria: Fundamental criteria

        Returns:
            Score from 0-100
        """
        score = 0
        criteria_count = len(criteria)

        if criteria_count == 0:
            return 0

        points_per_criterion = 100 / criteria_count

        # Check each criterion
        for criterion, range_spec in criteria.items():
            field_value = stock.get(criterion)

            if field_value is None:
                continue

            if isinstance(range_spec, dict):
                min_val = range_spec.get('min')
                max_val = range_spec.get('max')

                meets_criterion = True
                if min_val is not None and field_value < min_val:
                    meets_criterion = False
                if max_val is not None and max_val != 999 and field_value > max_val:
                    meets_criterion = False

                if meets_criterion:
                    score += points_per_criterion

        return int(score)

    def _score_results(self, results: List[Dict[str, Any]],
                      pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate match scores and sort results.

        Args:
            results: List of matching stocks
            pattern: Pattern definition

        Returns:
            Sorted list with match scores
        """
        has_fundamental = bool(pattern.get('fundamental_criteria'))
        has_technical = bool(pattern.get('technical_criteria'))

        for result in results:
            fundamental_score = result.get('fundamental_score', 0)
            technical_score = result.get('technical_score', 0)

            # Calculate weighted match score
            if has_fundamental and has_technical:
                # Combined pattern: 60% fundamental, 40% technical
                match_score = int(fundamental_score * 0.6 + technical_score * 0.4)
            elif has_fundamental:
                # Pure fundamental
                match_score = fundamental_score
            else:
                # Pure technical
                match_score = technical_score

            result['match_score'] = match_score

        # Sort by match score (or custom sort field)
        sort_by = pattern.get('sort_by', 'match_score')

        if sort_by == 'match_score':
            results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        else:
            # Sort by specific field from fundamental data
            # Handle None values by treating them as 0
            results.sort(
                key=lambda x: x.get('matched_fundamentals', {}).get(sort_by, 0) or 0,
                reverse=True
            )

        return results

    def create_pattern(self, pattern_data: Dict[str, Any]) -> bool:
        """
        Create a new custom pattern.

        Args:
            pattern_data: Pattern definition

        Returns:
            True if successful
        """
        return self.storage.create_pattern(pattern_data)

    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing pattern.

        Args:
            pattern_id: Pattern identifier
            updates: Fields to update

        Returns:
            True if successful
        """
        return self.storage.update_pattern(pattern_id, updates)

    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Delete a custom pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            True if successful
        """
        return self.storage.delete_pattern(pattern_id)

    def list_patterns(self, include_custom: bool = True) -> List[Dict[str, Any]]:
        """
        List all available patterns.

        Args:
            include_custom: Include custom patterns

        Returns:
            List of patterns
        """
        return self.storage.get_all_patterns(include_custom=include_custom)

    def get_pattern_details(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern details or None if not found
        """
        return self.storage.get_pattern(pattern_id)
