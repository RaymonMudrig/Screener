"""
Ratio Calculators

Calculate financial ratios: liquidity, leverage, efficiency, and valuation
"""

from typing import Dict, Optional, Any

from ..utils.logger import get_logger

logger = get_logger(__name__)


class RatioCalculator:
    """Calculate financial ratios from fundamental data"""

    # =================================================================
    # LIQUIDITY RATIOS
    # =================================================================

    @staticmethod
    def current_ratio(current_assets: float, current_liabilities: float) -> Optional[float]:
        """
        Current Ratio = Current Assets / Current Liabilities

        Measures ability to pay short-term obligations
        Good: > 2.0
        Acceptable: > 1.0
        Poor: < 1.0
        """
        if current_liabilities is None or current_liabilities == 0:
            return None
        if current_assets is None:
            return None

        return current_assets / current_liabilities

    @staticmethod
    def quick_ratio(current_assets: float, inventories: float, current_liabilities: float) -> Optional[float]:
        """
        Quick Ratio (Acid Test) = (Current Assets - Inventory) / Current Liabilities

        More conservative than current ratio
        Good: > 1.0
        Acceptable: > 0.5
        """
        if current_liabilities is None or current_liabilities == 0:
            return None
        if current_assets is None:
            return None

        inventory = inventories if inventories else 0
        return (current_assets - inventory) / current_liabilities

    @staticmethod
    def cash_ratio(cash: float, current_liabilities: float) -> Optional[float]:
        """
        Cash Ratio = Cash / Current Liabilities

        Most conservative liquidity ratio
        Good: > 0.5
        """
        if current_liabilities is None or current_liabilities == 0:
            return None
        if cash is None:
            return None

        return cash / current_liabilities

    @staticmethod
    def working_capital(current_assets: float, current_liabilities: float) -> Optional[float]:
        """
        Working Capital = Current Assets - Current Liabilities

        Positive is good
        """
        if current_assets is None or current_liabilities is None:
            return None

        return current_assets - current_liabilities

    @staticmethod
    def working_capital_ratio(current_assets: float, current_liabilities: float, total_assets: float) -> Optional[float]:
        """
        Working Capital Ratio = Working Capital / Total Assets

        Good: > 0.2
        """
        if total_assets is None or total_assets == 0:
            return None

        wc = RatioCalculator.working_capital(current_assets, current_liabilities)
        if wc is None:
            return None

        return wc / total_assets

    # =================================================================
    # LEVERAGE RATIOS
    # =================================================================

    @staticmethod
    def debt_to_assets(total_liabilities: float, total_assets: float) -> Optional[float]:
        """
        Debt-to-Assets = Total Liabilities / Total Assets

        Good: < 0.5
        Acceptable: < 0.7
        High risk: > 0.7
        """
        if total_assets is None or total_assets == 0:
            return None
        if total_liabilities is None:
            return None

        return total_liabilities / total_assets

    @staticmethod
    def equity_ratio(total_equity: float, total_assets: float) -> Optional[float]:
        """
        Equity Ratio = Total Equity / Total Assets

        Good: > 0.5
        Complement of debt-to-assets ratio
        """
        if total_assets is None or total_assets == 0:
            return None
        if total_equity is None:
            return None

        return total_equity / total_assets

    @staticmethod
    def financial_leverage(total_assets: float, total_equity: float) -> Optional[float]:
        """
        Financial Leverage = Total Assets / Total Equity

        Part of DuPont analysis
        Higher = more leveraged
        """
        if total_equity is None or total_equity == 0:
            return None
        if total_assets is None:
            return None

        return total_assets / total_equity

    @staticmethod
    def interest_coverage(operating_profit: float, interest_expense: float) -> Optional[float]:
        """
        Interest Coverage = Operating Profit / Interest Expense

        Good: > 5
        Acceptable: > 2.5
        Risky: < 1.5

        Note: Interest expense may need to be estimated
        """
        if interest_expense is None or interest_expense == 0:
            return None
        if operating_profit is None:
            return None

        return operating_profit / interest_expense

    # =================================================================
    # EFFICIENCY RATIOS
    # =================================================================

    @staticmethod
    def inventory_turnover(cost_of_goods_sold: float, inventory: float) -> Optional[float]:
        """
        Inventory Turnover = COGS / Average Inventory

        Higher is generally better (faster inventory movement)
        Varies by industry
        """
        if inventory is None or inventory == 0:
            return None
        if cost_of_goods_sold is None:
            return None

        return cost_of_goods_sold / inventory

    @staticmethod
    def receivables_turnover(revenue: float, receivables: float) -> Optional[float]:
        """
        Receivables Turnover = Revenue / Accounts Receivable

        Higher is better (faster collection)
        """
        if receivables is None or receivables == 0:
            return None
        if revenue is None:
            return None

        return revenue / receivables

    @staticmethod
    def days_sales_outstanding(receivables: float, revenue: float, days: int = 90) -> Optional[float]:
        """
        Days Sales Outstanding = (Receivables / Revenue) * Days

        Lower is better (faster collection)
        """
        if revenue is None or revenue == 0:
            return None
        if receivables is None:
            return None

        return (receivables / revenue) * days

    @staticmethod
    def days_inventory_outstanding(inventory: float, cost_of_goods_sold: float, days: int = 90) -> Optional[float]:
        """
        Days Inventory Outstanding = (Inventory / COGS) * Days

        Lower is better (faster turnover)
        """
        if cost_of_goods_sold is None or cost_of_goods_sold == 0:
            return None
        if inventory is None:
            return None

        return (inventory / cost_of_goods_sold) * days

    # =================================================================
    # VALUATION RATIOS
    # =================================================================

    @staticmethod
    def price_to_sales(market_cap: float, revenue: float) -> Optional[float]:
        """
        P/S Ratio = Market Cap / Revenue

        Lower is better for value investors
        Good: < 2
        Varies by industry
        """
        if revenue is None or revenue == 0:
            return None
        if market_cap is None:
            return None

        return market_cap / revenue

    @staticmethod
    def price_to_cash_flow(market_cap: float, operating_cash_flow: float) -> Optional[float]:
        """
        P/CF Ratio = Market Cap / Operating Cash Flow

        Lower is better
        Good: < 15
        """
        if operating_cash_flow is None or operating_cash_flow == 0:
            return None
        if market_cap is None:
            return None

        return market_cap / operating_cash_flow

    @staticmethod
    def market_cap(price: float, shares_outstanding: float) -> Optional[float]:
        """
        Market Cap = Price × Shares Outstanding
        """
        if price is None or shares_outstanding is None:
            return None

        return price * shares_outstanding

    @staticmethod
    def enterprise_value(market_cap: float, total_liabilities: float, cash: float) -> Optional[float]:
        """
        Enterprise Value = Market Cap + Debt - Cash

        Approximation using total liabilities as debt proxy
        """
        if market_cap is None:
            return None

        debt = total_liabilities if total_liabilities else 0
        cash_value = cash if cash else 0

        return market_cap + debt - cash_value

    @staticmethod
    def ev_to_ebitda(enterprise_value: float, operating_profit: float, depreciation: float = None) -> Optional[float]:
        """
        EV/EBITDA = Enterprise Value / EBITDA

        EBITDA approximated as Operating Profit (if depreciation not available)
        Good: < 12
        Varies by industry
        """
        if operating_profit is None or operating_profit == 0:
            return None
        if enterprise_value is None:
            return None

        # If depreciation available, add to operating profit to get EBITDA
        ebitda = operating_profit
        if depreciation:
            ebitda += depreciation

        return enterprise_value / ebitda

    @staticmethod
    def pe_ratio_realtime(latest_price: float, eps: float) -> Optional[float]:
        """
        P/E Ratio (Real-time) = Latest Market Price / EPS

        Calculate P/E ratio using the most recent market price
        instead of quarterly report price.

        Good: < 15
        Fair: 15-25
        Expensive: > 25
        """
        if eps is None or eps <= 0:
            return None
        if latest_price is None or latest_price <= 0:
            return None

        return latest_price / eps

    @staticmethod
    def pb_ratio_realtime(latest_price: float, book_value_per_share: float) -> Optional[float]:
        """
        P/B Ratio (Real-time) = Latest Market Price / Book Value Per Share

        Calculate P/B ratio using the most recent market price
        instead of quarterly report price.

        Good: < 1.0 (undervalued)
        Fair: 1.0-3.0
        Expensive: > 3.0
        """
        if book_value_per_share is None or book_value_per_share <= 0:
            return None
        if latest_price is None or latest_price <= 0:
            return None

        return latest_price / book_value_per_share

    @staticmethod
    def peg_ratio(pe_ratio: float, eps_growth_rate: float) -> Optional[float]:
        """
        PEG Ratio = P/E Ratio / EPS Growth Rate

        Good: < 1.0 (undervalued relative to growth)
        Fair: 1.0 - 2.0
        Expensive: > 2.0
        """
        if eps_growth_rate is None or eps_growth_rate == 0:
            return None
        if pe_ratio is None:
            return None

        return pe_ratio / eps_growth_rate

    # =================================================================
    # PROFITABILITY RATIOS (additional)
    # =================================================================

    @staticmethod
    def roic(net_income: float, total_equity: float, total_liabilities: float) -> Optional[float]:
        """
        Return on Invested Capital = Net Income / (Equity + Debt)

        Good: > 12%
        Excellent: > 20%
        """
        if total_equity is None:
            return None
        if net_income is None:
            return None

        invested_capital = total_equity
        if total_liabilities:
            invested_capital += total_liabilities

        if invested_capital == 0:
            return None

        return (net_income / invested_capital) * 100

    @staticmethod
    def gross_profit_margin(gross_profit: float, revenue: float) -> Optional[float]:
        """
        Gross Profit Margin = (Gross Profit / Revenue) * 100

        Higher is better
        Good: > 40%
        """
        if revenue is None or revenue == 0:
            return None
        if gross_profit is None:
            return None

        return (gross_profit / revenue) * 100

    # =================================================================
    # COMBINED CALCULATIONS
    # =================================================================

    def calculate_liquidity_ratios(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all liquidity ratios"""
        ratios = {}

        current_r = self.current_ratio(
            data.get('current_assets'),
            data.get('current_liabilities')
        )
        if current_r is not None:
            ratios['current_ratio'] = current_r

        quick_r = self.quick_ratio(
            data.get('current_assets'),
            data.get('inventories'),
            data.get('current_liabilities')
        )
        if quick_r is not None:
            ratios['quick_ratio'] = quick_r

        cash_r = self.cash_ratio(
            data.get('cash_end'),
            data.get('current_liabilities')
        )
        if cash_r is not None:
            ratios['cash_ratio'] = cash_r

        wc = self.working_capital(
            data.get('current_assets'),
            data.get('current_liabilities')
        )
        if wc is not None:
            ratios['working_capital'] = wc

        wc_ratio = self.working_capital_ratio(
            data.get('current_assets'),
            data.get('current_liabilities'),
            data.get('total_assets')
        )
        if wc_ratio is not None:
            ratios['working_capital_ratio'] = wc_ratio

        return ratios

    def calculate_leverage_ratios(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all leverage ratios"""
        ratios = {}

        # D/E ratio already provided, but calculate D/A
        d_to_a = self.debt_to_assets(
            data.get('total_liabilities'),
            data.get('total_assets')
        )
        if d_to_a is not None:
            ratios['debt_to_assets'] = d_to_a

        eq_ratio = self.equity_ratio(
            data.get('total_equity'),
            data.get('total_assets')
        )
        if eq_ratio is not None:
            ratios['equity_ratio'] = eq_ratio

        fin_lev = self.financial_leverage(
            data.get('total_assets'),
            data.get('total_equity')
        )
        if fin_lev is not None:
            ratios['financial_leverage'] = fin_lev

        return ratios

    def calculate_efficiency_ratios(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all efficiency ratios"""
        ratios = {}

        inv_turn = self.inventory_turnover(
            data.get('cost_of_goods_sold'),
            data.get('inventories')
        )
        if inv_turn is not None:
            ratios['inventory_turnover'] = inv_turn

        rec_turn = self.receivables_turnover(
            data.get('revenue'),
            data.get('receivables')
        )
        if rec_turn is not None:
            ratios['receivables_turnover'] = rec_turn

        dso = self.days_sales_outstanding(
            data.get('receivables'),
            data.get('revenue')
        )
        if dso is not None:
            ratios['days_sales_outstanding'] = dso

        dio = self.days_inventory_outstanding(
            data.get('inventories'),
            data.get('cost_of_goods_sold')
        )
        if dio is not None:
            ratios['days_inventory_outstanding'] = dio

        return ratios

    def calculate_valuation_ratios(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all valuation ratios"""
        ratios = {}

        # Calculate market cap first
        mcap = self.market_cap(
            data.get('close_price'),
            data.get('shares_outstanding')
        )

        if mcap:
            ratios['market_cap'] = mcap

            # P/S
            p_to_s = self.price_to_sales(mcap, data.get('revenue'))
            if p_to_s is not None:
                ratios['price_to_sales'] = p_to_s

            # P/CF
            p_to_cf = self.price_to_cash_flow(mcap, data.get('cf_operating'))
            if p_to_cf is not None:
                ratios['price_to_cash_flow'] = p_to_cf

            # EV
            ev = self.enterprise_value(
                mcap,
                data.get('total_liabilities'),
                data.get('cash_end')
            )
            if ev is not None:
                ratios['enterprise_value'] = ev

                # EV/EBITDA
                ev_ebitda = self.ev_to_ebitda(ev, data.get('operating_profit'))
                if ev_ebitda is not None:
                    ratios['ev_to_ebitda'] = ev_ebitda

        return ratios

    def calculate_all_ratios(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate all financial ratios"""
        all_ratios = {}

        all_ratios.update(self.calculate_liquidity_ratios(data))
        all_ratios.update(self.leverage_ratios(data))
        all_ratios.update(self.calculate_efficiency_ratios(data))
        all_ratios.update(self.calculate_valuation_ratios(data))

        # Add ROIC
        roic = self.roic(
            data.get('net_income'),
            data.get('total_equity'),
            data.get('total_liabilities')
        )
        if roic is not None:
            all_ratios['roic'] = roic

        return all_ratios
