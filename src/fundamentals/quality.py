"""
Quality Score Calculators

Calculate composite quality scores:
- Piotroski F-Score (9-point financial strength)
- Altman Z-Score (bankruptcy prediction)
- Cash quality metrics
"""

from typing import Dict, Optional, Any, List

from ..utils.logger import get_logger

logger = get_logger(__name__)


class QualityScorer:
    """Calculate financial quality scores"""

    # =================================================================
    # PIOTROSKI F-SCORE (9-point scale)
    # =================================================================

    def piotroski_f_score(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any] = None
    ) -> tuple[int, Dict[str, int]]:
        """
        Calculate Piotroski F-Score (0-9)

        Criteria (9 total):
        Profitability (4 points):
          1. ROA > 0
          2. Operating Cash Flow > 0
          3. ROA increasing
          4. Cash Flow > Net Income (quality of earnings)

        Leverage/Liquidity (3 points):
          5. Debt/Equity decreasing
          6. Current Ratio increasing
          7. No new shares issued

        Operating Efficiency (2 points):
          8. Gross Margin increasing
          9. Asset Turnover increasing

        Score Interpretation:
          8-9: Strong/High Quality
          5-7: Average/Moderate
          0-4: Weak/Low Quality

        Args:
            current: Current quarter data
            previous: Previous year same quarter data (for comparisons)

        Returns:
            Tuple of (total_score, component_scores)
        """
        score = 0
        components = {}

        # 1. ROA > 0
        roa = current.get('roa_percent', 0)
        if roa and roa > 0:
            score += 1
            components['positive_roa'] = 1
        else:
            components['positive_roa'] = 0

        # 2. Operating Cash Flow > 0
        cf_operating = current.get('cf_operating', 0)
        if cf_operating and cf_operating > 0:
            score += 1
            components['positive_ocf'] = 1
        else:
            components['positive_ocf'] = 0

        # If we have previous year data, calculate changes
        if previous:
            # 3. ROA increasing
            prev_roa = previous.get('roa_percent', 0)
            if roa and prev_roa and roa > prev_roa:
                score += 1
                components['roa_increasing'] = 1
            else:
                components['roa_increasing'] = 0

            # 4. Cash Flow > Net Income (accrual quality)
            net_income = current.get('net_income', 0)
            if cf_operating and net_income and cf_operating > net_income:
                score += 1
                components['quality_of_earnings'] = 1
            else:
                components['quality_of_earnings'] = 0

            # 5. Debt/Equity decreasing
            current_de = current.get('debt_equity_ratio')
            prev_de = previous.get('debt_equity_ratio')
            if current_de and prev_de and current_de < prev_de:
                score += 1
                components['leverage_decreasing'] = 1
            else:
                components['leverage_decreasing'] = 0

            # 6. Current Ratio increasing
            # Calculate current ratios
            current_cr = None
            prev_cr = None

            if current.get('current_assets') and current.get('current_liabilities'):
                if current['current_liabilities'] > 0:
                    current_cr = current['current_assets'] / current['current_liabilities']

            if previous.get('current_assets') and previous.get('current_liabilities'):
                if previous['current_liabilities'] > 0:
                    prev_cr = previous['current_assets'] / previous['current_liabilities']

            if current_cr and prev_cr and current_cr > prev_cr:
                score += 1
                components['liquidity_increasing'] = 1
            else:
                components['liquidity_increasing'] = 0

            # 7. No new shares issued (shares outstanding not increasing)
            current_shares = current.get('shares_outstanding')
            prev_shares = previous.get('shares_outstanding')

            if current_shares and prev_shares:
                if current_shares <= prev_shares:
                    score += 1
                    components['no_dilution'] = 1
                else:
                    components['no_dilution'] = 0
            else:
                components['no_dilution'] = 0

            # 8. Gross Margin increasing
            current_gm = current.get('gross_margin_percent')
            prev_gm = previous.get('gross_margin_percent')

            if current_gm and prev_gm and current_gm > prev_gm:
                score += 1
                components['margin_increasing'] = 1
            else:
                components['margin_increasing'] = 0

            # 9. Asset Turnover increasing
            current_at = current.get('asset_turnover')
            prev_at = previous.get('asset_turnover')

            if current_at and prev_at and current_at > prev_at:
                score += 1
                components['efficiency_increasing'] = 1
            else:
                components['efficiency_increasing'] = 0

        logger.debug(f"Piotroski F-Score: {score}/9")
        return score, components

    # =================================================================
    # ALTMAN Z-SCORE (Bankruptcy Prediction)
    # =================================================================

    def altman_z_score(self, data: Dict[str, Any]) -> Optional[float]:
        """
        Calculate Altman Z-Score for bankruptcy prediction

        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5

        Where:
          X1 = Working Capital / Total Assets
          X2 = Retained Earnings / Total Assets
          X3 = EBIT / Total Assets
          X4 = Market Value of Equity / Total Liabilities
          X5 = Sales / Total Assets

        Interpretation:
          Z > 3.0: Safe zone (low bankruptcy risk)
          2.7 - 3.0: Grey zone
          1.8 - 2.7: Distress zone
          Z < 1.8: High bankruptcy risk

        Args:
            data: Quarterly fundamental data

        Returns:
            Z-Score or None if cannot calculate
        """
        total_assets = data.get('total_assets')
        if not total_assets or total_assets == 0:
            return None

        # X1 = Working Capital / Total Assets
        current_assets = data.get('current_assets', 0)
        current_liabilities = data.get('current_liabilities', 0)
        working_capital = current_assets - current_liabilities
        x1 = working_capital / total_assets

        # X2 = Retained Earnings / Total Assets
        retained_earnings = data.get('retained_earnings', 0)
        x2 = retained_earnings / total_assets

        # X3 = EBIT / Total Assets (use operating_profit as EBIT proxy)
        ebit = data.get('operating_profit', 0)
        x3 = ebit / total_assets

        # X4 = Market Value of Equity / Total Liabilities
        market_cap = None
        if data.get('close_price') and data.get('shares_outstanding'):
            market_cap = data['close_price'] * data['shares_outstanding']

        total_liabilities = data.get('total_liabilities', 1)  # Avoid division by zero
        if total_liabilities == 0:
            total_liabilities = 1

        if market_cap:
            x4 = market_cap / total_liabilities
        else:
            # Fallback: use book value of equity
            total_equity = data.get('total_equity', 0)
            x4 = total_equity / total_liabilities

        # X5 = Sales / Total Assets
        sales = data.get('revenue', 0)
        x5 = sales / total_assets

        # Calculate Z-Score
        z_score = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5

        logger.debug(f"Altman Z-Score: {z_score:.2f}")
        return z_score

    def interpret_z_score(self, z_score: float) -> str:
        """
        Interpret Altman Z-Score

        Args:
            z_score: Calculated Z-Score

        Returns:
            Interpretation string
        """
        if z_score > 3.0:
            return "Safe Zone (Low Risk)"
        elif z_score >= 2.7:
            return "Grey Zone (Moderate Risk)"
        elif z_score >= 1.8:
            return "Distress Zone (High Risk)"
        else:
            return "High Bankruptcy Risk"

    # =================================================================
    # CASH QUALITY METRICS
    # =================================================================

    @staticmethod
    def cash_quality_score(operating_cash_flow: float, net_income: float) -> Optional[float]:
        """
        Cash Quality = Operating Cash Flow / Net Income

        Good: > 1.0 (cash earnings exceed accrual earnings)
        Warning: < 0.8
        """
        if net_income is None or net_income == 0:
            return None
        if operating_cash_flow is None:
            return None

        return operating_cash_flow / net_income

    @staticmethod
    def cash_flow_margin(operating_cash_flow: float, revenue: float) -> Optional[float]:
        """
        Cash Flow Margin = Operating Cash Flow / Revenue

        Good: > 10%
        """
        if revenue is None or revenue == 0:
            return None
        if operating_cash_flow is None:
            return None

        return (operating_cash_flow / revenue) * 100

    @staticmethod
    def free_cash_flow(operating_cash_flow: float, capital_expenditure: float) -> Optional[float]:
        """
        Free Cash Flow = Operating Cash Flow - Capital Expenditure

        Note: CapEx may need to be estimated from change in fixed assets
        """
        if operating_cash_flow is None:
            return None

        capex = capital_expenditure if capital_expenditure else 0
        return operating_cash_flow - capex

    @staticmethod
    def fcf_yield(free_cash_flow: float, market_cap: float) -> Optional[float]:
        """
        FCF Yield = Free Cash Flow / Market Cap

        Good: > 5%
        """
        if market_cap is None or market_cap == 0:
            return None
        if free_cash_flow is None:
            return None

        return (free_cash_flow / market_cap) * 100

    # =================================================================
    # PROFITABILITY CONSISTENCY
    # =================================================================

    def profitability_consistency(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Measure profitability consistency

        Args:
            quarters: List of quarterly data (newest first)

        Returns:
            Dict with consistency metrics
        """
        if not quarters or len(quarters) < 4:
            return {}

        consistency = {}

        # Count profitable quarters
        profitable_quarters = sum(
            1 for q in quarters
            if q.get('net_income') and q.get('net_income') > 0
        )
        consistency['profitable_quarters'] = profitable_quarters
        consistency['profitable_quarters_pct'] = (profitable_quarters / len(quarters)) * 100

        # Count positive cash flow quarters
        positive_cf_quarters = sum(
            1 for q in quarters
            if q.get('cf_operating') and q.get('cf_operating') > 0
        )
        consistency['positive_cf_quarters'] = positive_cf_quarters

        # ROE volatility (standard deviation)
        roe_values = [q.get('roe_percent') for q in quarters if q.get('roe_percent')]
        if len(roe_values) >= 4:
            import statistics
            roe_std = statistics.stdev(roe_values)
            roe_mean = statistics.mean(roe_values)
            consistency['roe_volatility'] = roe_std
            consistency['roe_stability'] = 100 - min((roe_std / roe_mean) * 100, 100) if roe_mean > 0 else 0

        return consistency

    # =================================================================
    # COMBINED QUALITY SCORE
    # =================================================================

    def comprehensive_quality_score(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any] = None,
        quarters: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive quality score

        Args:
            current: Current quarter data
            previous: Previous year data
            quarters: Historical quarters for consistency

        Returns:
            Dict with all quality metrics
        """
        quality_metrics = {}

        # Piotroski F-Score
        if previous:
            f_score, f_components = self.piotroski_f_score(current, previous)
            quality_metrics['piotroski_score'] = f_score
            quality_metrics['piotroski_components'] = f_components

        # Altman Z-Score
        z_score = self.altman_z_score(current)
        if z_score:
            quality_metrics['altman_z_score'] = z_score
            quality_metrics['z_score_interpretation'] = self.interpret_z_score(z_score)

        # Cash Quality
        cash_quality = self.cash_quality_score(
            current.get('cf_operating'),
            current.get('net_income')
        )
        if cash_quality:
            quality_metrics['cash_quality_ratio'] = cash_quality

        cf_margin = self.cash_flow_margin(
            current.get('cf_operating'),
            current.get('revenue')
        )
        if cf_margin:
            quality_metrics['cash_flow_margin'] = cf_margin

        # Profitability Consistency
        if quarters and len(quarters) >= 4:
            consistency = self.profitability_consistency(quarters)
            quality_metrics.update(consistency)

        return quality_metrics
