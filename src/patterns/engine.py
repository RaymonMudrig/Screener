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
        # Use existing screener methods based on criteria
        results = []

        # Check for common screening patterns
        if 'peg_ratio' in criteria and 'eps_growth_yoy' in criteria and 'roe_percent' in criteria:
            # GARP pattern
            max_peg = criteria['peg_ratio'].get('max', 1.0)
            min_growth = criteria['eps_growth_yoy'].get('min', 10.0)
            min_roe = criteria['roe_percent'].get('min', 12.0)
            results = self.fundamental_screener.screen_garp(max_peg, min_growth, min_roe)

        elif 'roic' in criteria and 'ev_ebitda' in criteria:
            # Magic Formula pattern
            min_roic = criteria['roic'].get('min', 12.0)
            max_ev = criteria['ev_ebitda'].get('max', 15.0)
            results = self.fundamental_screener.screen_magic_formula(min_roic, max_ev)

        elif 'piotroski_score' in criteria and 'current_ratio' in criteria and 'debt_to_assets' in criteria:
            # Financial Strength pattern
            # Note: screen_financial_strength uses fixed criteria
            results = self.fundamental_screener.screen_financial_strength()

        elif 'pe_ratio' in criteria:
            # Value pattern with P/E
            max_pe = criteria['pe_ratio'].get('max', 15.0)
            results = self.fundamental_screener.screen_low_pe(max_pe, 0)

        elif 'pb_ratio' in criteria:
            # Value pattern with P/B
            max_pb = criteria['pb_ratio'].get('max', 1.5)
            results = self.fundamental_screener.screen_low_pb(max_pb, 0)

        elif 'roe_percent' in criteria:
            # Quality pattern with ROE
            min_roe = criteria['roe_percent'].get('min', 15.0)
            results = self.fundamental_screener.screen_high_roe(min_roe)

        elif 'piotroski_score' in criteria:
            # Quality pattern with Piotroski
            min_score = criteria['piotroski_score'].get('min', 7)
            results = self.fundamental_screener.screen_high_piotroski(min_score)

        elif 'revenue_growth_yoy' in criteria:
            # Growth pattern
            min_growth = criteria['revenue_growth_yoy'].get('min', 20.0)
            results = self.fundamental_screener.screen_revenue_growth(min_growth)

        elif 'current_ratio' in criteria:
            # Liquidity pattern
            min_current = criteria['current_ratio'].get('min', 2.0)
            results = self.fundamental_screener.screen_strong_liquidity(min_current)

        elif 'debt_to_assets' in criteria or 'debt_to_equity' in criteria:
            # Low debt pattern
            max_debt = criteria.get('debt_to_assets', {}).get('max', 0.4)
            results = self.fundamental_screener.screen_low_debt(max_debt)

        # Format results for pattern engine
        formatted_results = []
        for stock in results:
            formatted_results.append({
                'stock_id': stock.get('stock_id'),
                'pe_ratio': stock.get('pe_ratio'),
                'pb_ratio': stock.get('pb_ratio'),
                'roe_percent': stock.get('roe_percent'),
                'revenue_growth_yoy': stock.get('revenue_growth_yoy'),
                'eps_growth_yoy': stock.get('eps_growth_yoy'),
                'piotroski_score': stock.get('piotroski_score'),
                'peg_ratio': stock.get('peg_ratio'),
                'roic': stock.get('roic'),
                'score': 80  # Default good score for matches
            })

        return formatted_results

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
            has_required_signal = any(
                sig.replace('_', ' ') in ' '.join(signal_names)
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
