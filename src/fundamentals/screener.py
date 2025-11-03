"""
Fundamental Screener

Screen stocks based on fundamental criteria:
- Value signals (low P/E, P/B, high yield)
- Growth signals (revenue/EPS growth, acceleration)
- Quality signals (Piotroski, ROE, margins)
- Health signals (liquidity, debt, Z-Score)
- Composite screeners (GARP, Magic Formula, etc.)
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.db import DatabaseManager
from .storage import FundamentalDataStorage
from .growth import GrowthCalculator
from .ratios import RatioCalculator
from .quality import QualityScorer
from .ttm import TTMCalculator

logger = get_logger(__name__)


class FundamentalScreener:
    """Screen stocks based on fundamental criteria"""

    def __init__(self, db_path: str = None):
        """Initialize screener"""
        if db_path is None:
            from ..utils.config import get_config
            config = get_config()
            db_path = config.get('database.path', 'database/stockCode.sqlite')

        self.db = DatabaseManager(db_path)
        self.storage = FundamentalDataStorage(db_path)
        self.growth_calc = GrowthCalculator()
        self.ratio_calc = RatioCalculator()
        self.quality_scorer = QualityScorer()
        self.ttm_calc = TTMCalculator(db_path)

    # =================================================================
    # VALUE SIGNALS
    # =================================================================

    def screen_low_pe(self, max_pe: float = 15.0, min_earnings: float = 0) -> List[Dict[str, Any]]:
        """
        Screen for low P/E ratio stocks (value investing)

        Args:
            max_pe: Maximum P/E ratio (default 15)
            min_earnings: Minimum earnings (filter out negative/tiny earnings)

        Returns:
            List of stocks matching criteria
        """
        query = """
            SELECT DISTINCT f.stock_id, f.pe_ratio, f.eps, f.close_price,
                   f.revenue, f.net_income, f.roe_percent
            FROM fundamental_data f
            INNER JOIN (
                SELECT stock_id, MAX(year || '-' || quarter) as latest
                FROM fundamental_data
                GROUP BY stock_id
            ) latest ON f.stock_id = latest.stock_id
                AND (f.year || '-' || f.quarter) = latest.latest
            WHERE f.pe_ratio IS NOT NULL
                AND f.pe_ratio > 0
                AND f.pe_ratio <= ?
                AND f.net_income >= ?
            ORDER BY f.pe_ratio ASC
        """

        results = self.db.execute_query(query, (max_pe, min_earnings))

        logger.info(f"Found {len(results)} stocks with P/E <= {max_pe}")
        return [dict(r) for r in results]

    def screen_low_pb(self, max_pb: float = 1.5, min_equity: float = 0) -> List[Dict[str, Any]]:
        """
        Screen for low P/B ratio stocks (below book value)

        Args:
            max_pb: Maximum P/B ratio (default 1.5, <1.0 = below book)
            min_equity: Minimum equity (filter out negative equity)

        Returns:
            List of stocks matching criteria
        """
        query = """
            SELECT DISTINCT f.stock_id, f.pb_ratio, f.book_value, f.close_price,
                   f.total_equity, f.roe_percent, f.roa_percent
            FROM fundamental_data f
            INNER JOIN (
                SELECT stock_id, MAX(year || '-' || quarter) as latest
                FROM fundamental_data
                GROUP BY stock_id
            ) latest ON f.stock_id = latest.stock_id
                AND (f.year || '-' || f.quarter) = latest.latest
            WHERE f.pb_ratio IS NOT NULL
                AND f.pb_ratio > 0
                AND f.pb_ratio <= ?
                AND f.total_equity >= ?
            ORDER BY f.pb_ratio ASC
        """

        results = self.db.execute_query(query, (max_pb, min_equity))

        logger.info(f"Found {len(results)} stocks with P/B <= {max_pb}")
        return [dict(r) for r in results]

    def screen_low_ps(self, max_ps: float = 2.0) -> List[Dict[str, Any]]:
        """
        Screen for low Price/Sales ratio stocks

        Args:
            max_ps: Maximum P/S ratio (default 2.0)

        Returns:
            List of stocks matching criteria
        """
        query = """
            SELECT f.stock_id, f.close_price, f.shares_outstanding, f.revenue,
                   (f.close_price * f.shares_outstanding / NULLIF(f.revenue, 0)) as ps_ratio,
                   f.npm_percent, f.roe_percent
            FROM fundamental_data f
            INNER JOIN (
                SELECT stock_id, MAX(year || '-' || quarter) as latest
                FROM fundamental_data
                GROUP BY stock_id
            ) latest ON f.stock_id = latest.stock_id
                AND (f.year || '-' || f.quarter) = latest.latest
            WHERE f.revenue > 0
                AND f.close_price IS NOT NULL
                AND f.shares_outstanding IS NOT NULL
                AND (f.close_price * f.shares_outstanding / f.revenue) <= ?
            ORDER BY ps_ratio ASC
        """

        results = self.db.execute_query(query, (max_ps,))

        logger.info(f"Found {len(results)} stocks with P/S <= {max_ps}")
        return [dict(r) for r in results]

    # =================================================================
    # GROWTH SIGNALS
    # =================================================================

    def screen_revenue_growth(
        self,
        min_growth_yoy: float = 20.0,
        min_quarters: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Screen for high revenue growth stocks

        Args:
            min_growth_yoy: Minimum YoY revenue growth % (default 20%)
            min_quarters: Minimum quarters of data required

        Returns:
            List of stocks with strong revenue growth
        """
        results = []

        # Get all stocks with enough data
        query = """
            SELECT DISTINCT stock_id
            FROM fundamental_data
            GROUP BY stock_id
            HAVING COUNT(*) >= ?
        """
        stocks = self.db.execute_query(query, (min_quarters + 4,))  # Need Q+4 for YoY

        for stock_row in stocks:
            stock_id = stock_row['stock_id']

            try:
                quarters = self.storage.get_quarters(stock_id, num_quarters=8)

                if len(quarters) < 5:  # Need at least 5 for YoY
                    continue

                # Calculate growth
                growth_metrics = self.growth_calc.calculate_revenue_growth(quarters)
                revenue_yoy = growth_metrics.get('revenue_growth_yoy')

                if revenue_yoy and revenue_yoy >= min_growth_yoy:
                    latest = quarters[0]
                    results.append({
                        'stock_id': stock_id,
                        'revenue_growth_yoy': revenue_yoy,
                        'revenue_growth_qoq': growth_metrics.get('revenue_growth_qoq'),
                        'revenue': latest.get('revenue'),
                        'npm_percent': latest.get('npm_percent'),
                        'roe_percent': latest.get('roe_percent')
                    })

            except Exception as e:
                logger.debug(f"Error calculating growth for {stock_id}: {e}")
                continue

        # Sort by YoY growth
        results.sort(key=lambda x: x.get('revenue_growth_yoy', 0), reverse=True)

        logger.info(f"Found {len(results)} stocks with revenue growth >= {min_growth_yoy}%")
        return results

    def screen_eps_growth(
        self,
        min_growth_yoy: float = 15.0,
        min_quarters: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Screen for high EPS growth stocks

        Args:
            min_growth_yoy: Minimum YoY EPS growth % (default 15%)
            min_quarters: Minimum quarters of data required

        Returns:
            List of stocks with strong EPS growth
        """
        results = []

        # Get all stocks with enough data
        query = """
            SELECT DISTINCT stock_id
            FROM fundamental_data
            GROUP BY stock_id
            HAVING COUNT(*) >= ?
        """
        stocks = self.db.execute_query(query, (min_quarters + 4,))

        for stock_row in stocks:
            stock_id = stock_row['stock_id']

            try:
                quarters = self.storage.get_quarters(stock_id, num_quarters=8)

                if len(quarters) < 5:
                    continue

                # Calculate growth
                growth_metrics = self.growth_calc.calculate_eps_growth(quarters)
                eps_yoy = growth_metrics.get('eps_growth_yoy')

                if eps_yoy and eps_yoy >= min_growth_yoy:
                    latest = quarters[0]
                    results.append({
                        'stock_id': stock_id,
                        'eps_growth_yoy': eps_yoy,
                        'eps_growth_qoq': growth_metrics.get('eps_growth_qoq'),
                        'eps': latest.get('eps'),
                        'pe_ratio': latest.get('pe_ratio'),
                        'roe_percent': latest.get('roe_percent')
                    })

            except Exception as e:
                logger.debug(f"Error calculating EPS growth for {stock_id}: {e}")
                continue

        # Sort by YoY growth
        results.sort(key=lambda x: x.get('eps_growth_yoy', 0), reverse=True)

        logger.info(f"Found {len(results)} stocks with EPS growth >= {min_growth_yoy}%")
        return results

    def screen_accelerating_growth(self) -> List[Dict[str, Any]]:
        """
        Screen for stocks with accelerating growth (growth rate increasing)

        Returns:
            List of stocks with accelerating revenue growth
        """
        results = []

        # Get all stocks with enough data
        query = """
            SELECT DISTINCT stock_id
            FROM fundamental_data
            GROUP BY stock_id
            HAVING COUNT(*) >= 6
        """
        stocks = self.db.execute_query(query)

        for stock_row in stocks:
            stock_id = stock_row['stock_id']

            try:
                quarters = self.storage.get_quarters(stock_id, num_quarters=8)

                if len(quarters) < 6:
                    continue

                # Check if revenue growth is accelerating
                is_accelerating = self.growth_calc.is_accelerating_growth(quarters, 'revenue')

                if is_accelerating:
                    latest = quarters[0]
                    growth_metrics = self.growth_calc.calculate_revenue_growth(quarters)

                    results.append({
                        'stock_id': stock_id,
                        'revenue_growth_yoy': growth_metrics.get('revenue_growth_yoy'),
                        'revenue_growth_qoq': growth_metrics.get('revenue_growth_qoq'),
                        'revenue': latest.get('revenue'),
                        'npm_percent': latest.get('npm_percent')
                    })

            except Exception as e:
                logger.debug(f"Error checking acceleration for {stock_id}: {e}")
                continue

        logger.info(f"Found {len(results)} stocks with accelerating growth")
        return results

    # =================================================================
    # QUALITY SIGNALS
    # =================================================================

    def screen_high_piotroski(self, min_score: int = 7) -> List[Dict[str, Any]]:
        """
        Screen for high Piotroski F-Score stocks (quality)

        Args:
            min_score: Minimum F-Score (default 7, range 0-9)

        Returns:
            List of high-quality stocks
        """
        results = []

        # Get all stocks with enough data
        query = """
            SELECT DISTINCT stock_id
            FROM fundamental_data
            GROUP BY stock_id
            HAVING COUNT(*) >= 5
        """
        stocks = self.db.execute_query(query)

        for stock_row in stocks:
            stock_id = stock_row['stock_id']

            try:
                quarters = self.storage.get_quarters(stock_id, num_quarters=8)

                if len(quarters) < 5:  # Need current + previous year (Q-4)
                    continue

                latest = quarters[0]
                previous_year = quarters[4]

                # Calculate Piotroski F-Score
                f_score, f_components = self.quality_scorer.piotroski_f_score(latest, previous_year)

                if f_score >= min_score:
                    results.append({
                        'stock_id': stock_id,
                        'piotroski_score': f_score,
                        'roe_percent': latest.get('roe_percent'),
                        'roa_percent': latest.get('roa_percent'),
                        'npm_percent': latest.get('npm_percent'),
                        'pe_ratio': latest.get('pe_ratio'),
                        'pb_ratio': latest.get('pb_ratio')
                    })

            except Exception as e:
                logger.debug(f"Error calculating Piotroski for {stock_id}: {e}")
                continue

        # Sort by F-Score
        results.sort(key=lambda x: x.get('piotroski_score', 0), reverse=True)

        logger.info(f"Found {len(results)} stocks with Piotroski >= {min_score}")
        return results

    def screen_high_roe(self, min_roe: float = 15.0) -> List[Dict[str, Any]]:
        """
        Screen for high ROE stocks

        Args:
            min_roe: Minimum ROE % (default 15%)

        Returns:
            List of stocks with high ROE
        """
        query = """
            SELECT DISTINCT f.stock_id, f.roe_percent, f.roa_percent,
                   f.npm_percent, f.pe_ratio, f.pb_ratio,
                   f.revenue, f.net_income, f.total_equity
            FROM fundamental_data f
            INNER JOIN (
                SELECT stock_id, MAX(year || '-' || quarter) as latest
                FROM fundamental_data
                GROUP BY stock_id
            ) latest ON f.stock_id = latest.stock_id
                AND (f.year || '-' || f.quarter) = latest.latest
            WHERE f.roe_percent IS NOT NULL
                AND f.roe_percent >= ?
                AND f.total_equity > 0
            ORDER BY f.roe_percent DESC
        """

        results = self.db.execute_query(query, (min_roe,))

        logger.info(f"Found {len(results)} stocks with ROE >= {min_roe}%")
        return [dict(r) for r in results]

    def screen_high_margins(self, min_npm: float = 15.0) -> List[Dict[str, Any]]:
        """
        Screen for high profit margin stocks

        Args:
            min_npm: Minimum net profit margin % (default 15%)

        Returns:
            List of stocks with high margins
        """
        query = """
            SELECT DISTINCT f.stock_id, f.npm_percent, f.opm_percent,
                   f.gross_margin_percent, f.roe_percent, f.roa_percent,
                   f.revenue, f.net_income, f.pe_ratio
            FROM fundamental_data f
            INNER JOIN (
                SELECT stock_id, MAX(year || '-' || quarter) as latest
                FROM fundamental_data
                GROUP BY stock_id
            ) latest ON f.stock_id = latest.stock_id
                AND (f.year || '-' || f.quarter) = latest.latest
            WHERE f.npm_percent IS NOT NULL
                AND f.npm_percent >= ?
            ORDER BY f.npm_percent DESC
        """

        results = self.db.execute_query(query, (min_npm,))

        logger.info(f"Found {len(results)} stocks with NPM >= {min_npm}%")
        return [dict(r) for r in results]

    # =================================================================
    # HEALTH SIGNALS
    # =================================================================

    def screen_strong_liquidity(self, min_current_ratio: float = 2.0) -> List[Dict[str, Any]]:
        """
        Screen for stocks with strong liquidity

        Args:
            min_current_ratio: Minimum current ratio (default 2.0)

        Returns:
            List of stocks with strong liquidity
        """
        query = """
            SELECT f.stock_id, f.current_assets, f.current_liabilities,
                   (f.current_assets / NULLIF(f.current_liabilities, 0)) as current_ratio,
                   f.total_assets, f.total_equity, f.roe_percent
            FROM fundamental_data f
            INNER JOIN (
                SELECT stock_id, MAX(year || '-' || quarter) as latest
                FROM fundamental_data
                GROUP BY stock_id
            ) latest ON f.stock_id = latest.stock_id
                AND (f.year || '-' || f.quarter) = latest.latest
            WHERE f.current_assets IS NOT NULL
                AND f.current_liabilities > 0
                AND (f.current_assets / f.current_liabilities) >= ?
            ORDER BY current_ratio DESC
        """

        results = self.db.execute_query(query, (min_current_ratio,))

        logger.info(f"Found {len(results)} stocks with Current Ratio >= {min_current_ratio}")
        return [dict(r) for r in results]

    def screen_low_debt(self, max_debt_to_assets: float = 0.4) -> List[Dict[str, Any]]:
        """
        Screen for low debt stocks

        Args:
            max_debt_to_assets: Maximum Debt/Assets ratio (default 0.4)

        Returns:
            List of stocks with low debt
        """
        query = """
            SELECT f.stock_id, f.total_liabilities, f.total_assets,
                   (f.total_liabilities / NULLIF(f.total_assets, 0)) as debt_to_assets,
                   f.total_equity, f.debt_equity_ratio, f.roe_percent
            FROM fundamental_data f
            INNER JOIN (
                SELECT stock_id, MAX(year || '-' || quarter) as latest
                FROM fundamental_data
                GROUP BY stock_id
            ) latest ON f.stock_id = latest.stock_id
                AND (f.year || '-' || f.quarter) = latest.latest
            WHERE f.total_assets > 0
                AND f.total_liabilities IS NOT NULL
                AND (f.total_liabilities / f.total_assets) <= ?
            ORDER BY debt_to_assets ASC
        """

        results = self.db.execute_query(query, (max_debt_to_assets,))

        logger.info(f"Found {len(results)} stocks with D/A <= {max_debt_to_assets}")
        return [dict(r) for r in results]

    def screen_safe_zscore(self, min_zscore: float = 3.0) -> List[Dict[str, Any]]:
        """
        Screen for financially safe stocks (Altman Z-Score)

        Args:
            min_zscore: Minimum Z-Score (default 3.0 = safe zone)

        Returns:
            List of financially safe stocks
        """
        results = []

        # Get all stocks
        query = """
            SELECT DISTINCT stock_id
            FROM fundamental_data
        """
        stocks = self.db.execute_query(query)

        for stock_row in stocks:
            stock_id = stock_row['stock_id']

            try:
                quarters = self.storage.get_quarters(stock_id, num_quarters=1)

                if not quarters:
                    continue

                latest = quarters[0]

                # Calculate Z-Score
                z_score = self.quality_scorer.altman_z_score(latest)

                if z_score and z_score >= min_zscore:
                    results.append({
                        'stock_id': stock_id,
                        'altman_z_score': z_score,
                        'total_assets': latest.get('total_assets'),
                        'total_equity': latest.get('total_equity'),
                        'revenue': latest.get('revenue'),
                        'roe_percent': latest.get('roe_percent')
                    })

            except Exception as e:
                logger.debug(f"Error calculating Z-Score for {stock_id}: {e}")
                continue

        # Sort by Z-Score
        results.sort(key=lambda x: x.get('altman_z_score', 0), reverse=True)

        logger.info(f"Found {len(results)} stocks with Z-Score >= {min_zscore}")
        return results

    def screen_positive_cash_flow(self) -> List[Dict[str, Any]]:
        """
        Screen for stocks with positive operating cash flow

        Returns:
            List of stocks with positive OCF
        """
        query = """
            SELECT f.stock_id, f.cf_operating, f.cf_investing, f.cf_financing,
                   f.net_income, f.revenue, f.roe_percent,
                   (f.cf_operating / NULLIF(f.net_income, 0)) as cash_quality
            FROM fundamental_data f
            INNER JOIN (
                SELECT stock_id, MAX(year || '-' || quarter) as latest
                FROM fundamental_data
                GROUP BY stock_id
            ) latest ON f.stock_id = latest.stock_id
                AND (f.year || '-' || f.quarter) = latest.latest
            WHERE f.cf_operating IS NOT NULL
                AND f.cf_operating > 0
            ORDER BY cash_quality DESC
        """

        results = self.db.execute_query(query)

        logger.info(f"Found {len(results)} stocks with positive OCF")
        return [dict(r) for r in results]

    # =================================================================
    # COMPOSITE SCREENERS
    # =================================================================

    def screen_garp(
        self,
        max_peg: float = 1.0,
        min_growth: float = 10.0,
        min_roe: float = 12.0
    ) -> List[Dict[str, Any]]:
        """
        GARP: Growth at Reasonable Price

        Criteria:
        - PEG ratio < 1.0 (growth cheaper than P/E suggests)
        - EPS growth > 10% YoY
        - ROE > 12%

        Args:
            max_peg: Maximum PEG ratio
            min_growth: Minimum EPS growth %
            min_roe: Minimum ROE %

        Returns:
            List of GARP stocks
        """
        results = []

        # Get all stocks with enough data
        query = """
            SELECT DISTINCT stock_id
            FROM fundamental_data
            GROUP BY stock_id
            HAVING COUNT(*) >= 5
        """
        stocks = self.db.execute_query(query)

        for stock_row in stocks:
            stock_id = stock_row['stock_id']

            try:
                quarters = self.storage.get_quarters(stock_id, num_quarters=8)

                if len(quarters) < 5:
                    continue

                latest = quarters[0]

                # Check ROE
                roe = latest.get('roe_percent')
                if not roe or roe < min_roe:
                    continue

                # Calculate EPS growth
                growth_metrics = self.growth_calc.calculate_eps_growth(quarters)
                eps_growth = growth_metrics.get('eps_growth_yoy')

                if not eps_growth or eps_growth < min_growth:
                    continue

                # Calculate PEG ratio
                pe_ratio = latest.get('pe_ratio')
                if not pe_ratio or pe_ratio <= 0:
                    continue

                peg = self.ratio_calc.peg_ratio(pe_ratio, eps_growth)

                if peg and peg <= max_peg:
                    results.append({
                        'stock_id': stock_id,
                        'peg_ratio': peg,
                        'pe_ratio': pe_ratio,
                        'eps_growth_yoy': eps_growth,
                        'roe_percent': roe,
                        'eps': latest.get('eps'),
                        'revenue': latest.get('revenue')
                    })

            except Exception as e:
                logger.debug(f"Error screening GARP for {stock_id}: {e}")
                continue

        # Sort by PEG ratio
        results.sort(key=lambda x: x.get('peg_ratio', 999))

        logger.info(f"Found {len(results)} GARP stocks (PEG<={max_peg}, Growth>={min_growth}%, ROE>={min_roe}%)")
        return results

    def screen_magic_formula(
        self,
        min_roic: float = 12.0,
        max_ev_ebitda: float = 15.0
    ) -> List[Dict[str, Any]]:
        """
        Magic Formula: Quality + Value (Joel Greenblatt)

        Criteria:
        - High ROIC (> 12%)
        - Low EV/EBITDA (< 15)

        Args:
            min_roic: Minimum ROIC %
            max_ev_ebitda: Maximum EV/EBITDA

        Returns:
            List of Magic Formula stocks
        """
        results = []

        # Get TTM metrics for better ROIC calculation
        query = """
            SELECT t.stock_id, t.ttm_roic, t.ttm_revenue, t.ttm_net_income,
                   f.close_price, f.shares_outstanding, f.total_liabilities,
                   f.cash_end, f.operating_profit
            FROM ttm_metrics t
            JOIN fundamental_data f ON t.stock_id = f.stock_id
            INNER JOIN (
                SELECT stock_id, MAX(year || '-' || quarter) as latest
                FROM fundamental_data
                GROUP BY stock_id
            ) latest ON f.stock_id = latest.stock_id
                AND (f.year || '-' || f.quarter) = latest.latest
            WHERE t.ttm_roic >= ?
                AND f.close_price IS NOT NULL
                AND f.shares_outstanding IS NOT NULL
                AND f.operating_profit > 0
        """

        stocks_with_roic = self.db.execute_query(query, (min_roic,))

        for stock in stocks_with_roic:
            try:
                # Calculate EV/EBITDA
                stock_dict = dict(stock)

                # Market cap
                mcap = self.ratio_calc.market_cap(
                    stock_dict.get('close_price'),
                    stock_dict.get('shares_outstanding')
                )

                if not mcap:
                    continue

                # Enterprise value
                ev = self.ratio_calc.enterprise_value(
                    mcap,
                    stock_dict.get('total_liabilities'),
                    stock_dict.get('cash_end')
                )

                if not ev:
                    continue

                # EV/EBITDA (using operating profit as EBITDA proxy)
                ev_ebitda = self.ratio_calc.ev_to_ebitda(
                    ev,
                    stock_dict.get('operating_profit')
                )

                if ev_ebitda and ev_ebitda <= max_ev_ebitda:
                    results.append({
                        'stock_id': stock_dict['stock_id'],
                        'roic': stock_dict['ttm_roic'],
                        'ev_ebitda': ev_ebitda,
                        'ttm_revenue': stock_dict['ttm_revenue'],
                        'ttm_net_income': stock_dict['ttm_net_income'],
                        'market_cap': mcap
                    })

            except Exception as e:
                logger.debug(f"Error screening Magic Formula for {stock.get('stock_id')}: {e}")
                continue

        # Sort by combined rank (lower is better)
        # Rank by ROIC (descending) and EV/EBITDA (ascending)
        results.sort(key=lambda x: (-x.get('roic', 0), x.get('ev_ebitda', 999)))

        logger.info(f"Found {len(results)} Magic Formula stocks (ROIC>={min_roic}%, EV/EBITDA<={max_ev_ebitda})")
        return results

    def screen_financial_strength(self) -> List[Dict[str, Any]]:
        """
        Financial Strength Composite Screen

        Criteria:
        - Piotroski F-Score >= 7
        - Current Ratio >= 2.0
        - Debt/Assets <= 0.5
        - Positive operating cash flow

        Returns:
            List of financially strong stocks
        """
        results = []

        # Get all stocks with enough data
        query = """
            SELECT DISTINCT stock_id
            FROM fundamental_data
            GROUP BY stock_id
            HAVING COUNT(*) >= 5
        """
        stocks = self.db.execute_query(query)

        for stock_row in stocks:
            stock_id = stock_row['stock_id']

            try:
                quarters = self.storage.get_quarters(stock_id, num_quarters=8)

                if len(quarters) < 5:
                    continue

                latest = quarters[0]
                previous_year = quarters[4]

                # Check Piotroski F-Score
                f_score, _ = self.quality_scorer.piotroski_f_score(latest, previous_year)
                if f_score < 7:
                    continue

                # Check Current Ratio
                current_ratio = self.ratio_calc.current_ratio(
                    latest.get('current_assets'),
                    latest.get('current_liabilities')
                )
                if not current_ratio or current_ratio < 2.0:
                    continue

                # Check Debt/Assets
                debt_to_assets = self.ratio_calc.debt_to_assets(
                    latest.get('total_liabilities'),
                    latest.get('total_assets')
                )
                if not debt_to_assets or debt_to_assets > 0.5:
                    continue

                # Check positive OCF
                ocf = latest.get('cf_operating')
                if not ocf or ocf <= 0:
                    continue

                results.append({
                    'stock_id': stock_id,
                    'piotroski_score': f_score,
                    'current_ratio': current_ratio,
                    'debt_to_assets': debt_to_assets,
                    'cf_operating': ocf,
                    'roe_percent': latest.get('roe_percent'),
                    'npm_percent': latest.get('npm_percent')
                })

            except Exception as e:
                logger.debug(f"Error screening financial strength for {stock_id}: {e}")
                continue

        # Sort by Piotroski score
        results.sort(key=lambda x: x.get('piotroski_score', 0), reverse=True)

        logger.info(f"Found {len(results)} financially strong stocks")
        return results
