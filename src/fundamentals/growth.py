"""
Growth Calculators

Calculate growth metrics: YoY, QoQ, CAGR for revenue, earnings, assets, etc.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import math

from ..utils.logger import get_logger

logger = get_logger(__name__)


class GrowthCalculator:
    """Calculate growth metrics from quarterly fundamental data"""

    @staticmethod
    def calculate_yoy_growth(current_value: float, previous_year_value: float) -> Optional[float]:
        """
        Calculate Year-over-Year growth percentage

        Args:
            current_value: Current quarter value
            previous_year_value: Same quarter, previous year value

        Returns:
            Growth percentage or None if cannot calculate
        """
        if previous_year_value is None or previous_year_value == 0:
            return None

        if current_value is None:
            return None

        return ((current_value - previous_year_value) / abs(previous_year_value)) * 100

    @staticmethod
    def calculate_qoq_growth(current_value: float, previous_quarter_value: float) -> Optional[float]:
        """
        Calculate Quarter-over-Quarter growth percentage

        Args:
            current_value: Current quarter value
            previous_quarter_value: Previous quarter value

        Returns:
            Growth percentage or None if cannot calculate
        """
        if previous_quarter_value is None or previous_quarter_value == 0:
            return None

        if current_value is None:
            return None

        return ((current_value - previous_quarter_value) / abs(previous_quarter_value)) * 100

    @staticmethod
    def calculate_cagr(start_value: float, end_value: float, num_periods: int) -> Optional[float]:
        """
        Calculate Compound Annual Growth Rate

        Args:
            start_value: Starting value
            end_value: Ending value
            num_periods: Number of periods (years)

        Returns:
            CAGR percentage or None if cannot calculate
        """
        if start_value is None or start_value <= 0:
            return None

        if end_value is None or end_value <= 0:
            return None

        if num_periods <= 0:
            return None

        try:
            cagr = (math.pow(end_value / start_value, 1 / num_periods) - 1) * 100
            return cagr
        except (ValueError, ZeroDivisionError):
            return None

    def calculate_revenue_growth(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate revenue growth metrics

        Args:
            quarters: List of quarterly data (newest first)

        Returns:
            Dictionary with growth metrics
        """
        if not quarters or len(quarters) < 2:
            return {}

        current = quarters[0]
        growth_metrics = {}

        # QoQ Growth (vs previous quarter)
        if len(quarters) >= 2:
            qoq = self.calculate_qoq_growth(
                current.get('revenue'),
                quarters[1].get('revenue')
            )
            growth_metrics['revenue_growth_qoq'] = qoq

        # YoY Growth (vs same quarter last year)
        if len(quarters) >= 5:  # Need Q+4 for YoY
            yoy = self.calculate_yoy_growth(
                current.get('revenue'),
                quarters[4].get('revenue')
            )
            growth_metrics['revenue_growth_yoy'] = yoy

        # CAGR (if we have 8+ quarters = 2 years)
        if len(quarters) >= 8:
            cagr = self.calculate_cagr(
                quarters[7].get('revenue'),  # 2 years ago
                current.get('revenue'),
                2  # 2 years
            )
            growth_metrics['revenue_cagr_2y'] = cagr

        return growth_metrics

    def calculate_eps_growth(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate EPS growth metrics

        Args:
            quarters: List of quarterly data (newest first)

        Returns:
            Dictionary with growth metrics
        """
        if not quarters or len(quarters) < 2:
            return {}

        current = quarters[0]
        growth_metrics = {}

        # QoQ Growth
        if len(quarters) >= 2:
            qoq = self.calculate_qoq_growth(
                current.get('eps'),
                quarters[1].get('eps')
            )
            growth_metrics['eps_growth_qoq'] = qoq

        # YoY Growth
        if len(quarters) >= 5:
            yoy = self.calculate_yoy_growth(
                current.get('eps'),
                quarters[4].get('eps')
            )
            growth_metrics['eps_growth_yoy'] = yoy

        # CAGR (2 years)
        if len(quarters) >= 8:
            cagr = self.calculate_cagr(
                quarters[7].get('eps'),
                current.get('eps'),
                2
            )
            growth_metrics['eps_cagr_2y'] = cagr

        return growth_metrics

    def calculate_net_income_growth(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate net income growth metrics"""
        if not quarters or len(quarters) < 2:
            return {}

        current = quarters[0]
        growth_metrics = {}

        # QoQ Growth
        if len(quarters) >= 2:
            qoq = self.calculate_qoq_growth(
                current.get('net_income'),
                quarters[1].get('net_income')
            )
            growth_metrics['net_income_growth_qoq'] = qoq

        # YoY Growth
        if len(quarters) >= 5:
            yoy = self.calculate_yoy_growth(
                current.get('net_income'),
                quarters[4].get('net_income')
            )
            growth_metrics['net_income_growth_yoy'] = yoy

        return growth_metrics

    def calculate_asset_growth(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate total assets growth"""
        if not quarters or len(quarters) < 2:
            return {}

        current = quarters[0]
        growth_metrics = {}

        # QoQ Growth
        if len(quarters) >= 2:
            qoq = self.calculate_qoq_growth(
                current.get('total_assets'),
                quarters[1].get('total_assets')
            )
            growth_metrics['asset_growth_qoq'] = qoq

        # YoY Growth
        if len(quarters) >= 5:
            yoy = self.calculate_yoy_growth(
                current.get('total_assets'),
                quarters[4].get('total_assets')
            )
            growth_metrics['asset_growth_yoy'] = yoy

        return growth_metrics

    def calculate_equity_growth(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate equity growth"""
        if not quarters or len(quarters) < 2:
            return {}

        current = quarters[0]
        growth_metrics = {}

        # QoQ Growth
        if len(quarters) >= 2:
            qoq = self.calculate_qoq_growth(
                current.get('total_equity'),
                quarters[1].get('total_equity')
            )
            growth_metrics['equity_growth_qoq'] = qoq

        # YoY Growth
        if len(quarters) >= 5:
            yoy = self.calculate_yoy_growth(
                current.get('total_equity'),
                quarters[4].get('total_equity')
            )
            growth_metrics['equity_growth_yoy'] = yoy

        return growth_metrics

    def calculate_operating_profit_growth(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate operating profit growth"""
        if not quarters or len(quarters) < 2:
            return {}

        current = quarters[0]
        growth_metrics = {}

        # QoQ Growth
        if len(quarters) >= 2:
            qoq = self.calculate_qoq_growth(
                current.get('operating_profit'),
                quarters[1].get('operating_profit')
            )
            growth_metrics['operating_profit_growth_qoq'] = qoq

        # YoY Growth
        if len(quarters) >= 5:
            yoy = self.calculate_yoy_growth(
                current.get('operating_profit'),
                quarters[4].get('operating_profit')
            )
            growth_metrics['operating_profit_growth_yoy'] = yoy

        return growth_metrics

    def calculate_margin_trends(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate margin trends (improving or deteriorating)

        Args:
            quarters: List of quarterly data (newest first)

        Returns:
            Dictionary with margin trend metrics
        """
        if not quarters or len(quarters) < 2:
            return {}

        trends = {}

        # Net Profit Margin trend
        if len(quarters) >= 2:
            current_npm = quarters[0].get('npm_percent')
            prev_npm = quarters[1].get('npm_percent')

            if current_npm and prev_npm:
                trends['npm_trend_qoq'] = current_npm - prev_npm

        if len(quarters) >= 5:
            current_npm = quarters[0].get('npm_percent')
            prev_year_npm = quarters[4].get('npm_percent')

            if current_npm and prev_year_npm:
                trends['npm_trend_yoy'] = current_npm - prev_year_npm

        # Operating Profit Margin trend
        if len(quarters) >= 2:
            current_opm = quarters[0].get('opm_percent')
            prev_opm = quarters[1].get('opm_percent')

            if current_opm and prev_opm:
                trends['opm_trend_qoq'] = current_opm - prev_opm

        if len(quarters) >= 5:
            current_opm = quarters[0].get('opm_percent')
            prev_year_opm = quarters[4].get('opm_percent')

            if current_opm and prev_year_opm:
                trends['opm_trend_yoy'] = current_opm - prev_year_opm

        # Gross Margin trend
        if len(quarters) >= 2:
            current_gm = quarters[0].get('gross_margin_percent')
            prev_gm = quarters[1].get('gross_margin_percent')

            if current_gm and prev_gm:
                trends['gross_margin_trend_qoq'] = current_gm - prev_gm

        return trends

    def calculate_all_growth_metrics(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate all growth metrics

        Args:
            quarters: List of quarterly data (newest first)

        Returns:
            Dictionary with all growth metrics
        """
        all_metrics = {}

        # Revenue growth
        all_metrics.update(self.calculate_revenue_growth(quarters))

        # EPS growth
        all_metrics.update(self.calculate_eps_growth(quarters))

        # Net income growth
        all_metrics.update(self.calculate_net_income_growth(quarters))

        # Asset growth
        all_metrics.update(self.calculate_asset_growth(quarters))

        # Equity growth
        all_metrics.update(self.calculate_equity_growth(quarters))

        # Operating profit growth
        all_metrics.update(self.calculate_operating_profit_growth(quarters))

        # Margin trends
        all_metrics.update(self.calculate_margin_trends(quarters))

        return all_metrics

    def is_accelerating_growth(self, quarters: List[Dict[str, Any]], metric: str = 'revenue') -> Optional[bool]:
        """
        Check if growth is accelerating

        Args:
            quarters: List of quarterly data (newest first)
            metric: Metric to check ('revenue', 'eps', 'net_income')

        Returns:
            True if accelerating, False if decelerating, None if cannot determine
        """
        if len(quarters) < 6:  # Need at least 6 quarters
            return None

        field_map = {
            'revenue': 'revenue',
            'eps': 'eps',
            'net_income': 'net_income'
        }

        field = field_map.get(metric)
        if not field:
            return None

        # Calculate recent growth (Q0 vs Q4)
        recent_growth = self.calculate_yoy_growth(
            quarters[0].get(field),
            quarters[4].get(field)
        )

        # Calculate older growth (Q1 vs Q5)
        older_growth = self.calculate_yoy_growth(
            quarters[1].get(field),
            quarters[5].get(field)
        )

        if recent_growth is None or older_growth is None:
            return None

        return recent_growth > older_growth
