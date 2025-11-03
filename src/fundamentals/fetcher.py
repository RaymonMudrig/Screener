"""
Fundamental Data Fetcher

Fetches quarterly fundamental data from IDX Mobile API
API: https://idxmobile.co.id/Data/fd?isJSONStr=1&code={stockCode}:{year}:{quarter}
"""

import requests
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from urllib3.exceptions import InsecureRequestWarning

from ..utils.logger import get_logger

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

logger = get_logger(__name__)


class FundamentalDataFetcher:
    """Fetch quarterly fundamental data from IDX API"""

    BASE_URL = "https://idxmobile.co.id/Data/fd"

    def __init__(self, timeout: int = 30):
        """
        Initialize fetcher

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for self-signed cert

    def fetch_quarterly_data(
        self,
        stock_id: str,
        year: int,
        quarter: int
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch fundamental data for a specific quarter

        Args:
            stock_id: Stock code (e.g., "BBCA")
            year: Year (e.g., 2024)
            quarter: Quarter 1-4

        Returns:
            Dictionary with fundamental data or None if failed
        """
        if quarter < 1 or quarter > 4:
            logger.error(f"Invalid quarter: {quarter}. Must be 1-4")
            return None

        try:
            # Build URL
            url = f"{self.BASE_URL}?isJSONStr=1&code={stock_id}:{year}:{quarter}"

            logger.debug(f"Fetching {stock_id} Q{quarter} {year} from {url}")

            # Make request
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse JSON
            data = response.json()

            if not data or len(data) == 0:
                logger.warning(f"No data returned for {stock_id} Q{quarter} {year}")
                return None

            # IDX API returns array with single object
            fundamental_data = data[0]

            # Validate basic fields
            if fundamental_data.get('StockID') != stock_id:
                logger.warning(f"Stock ID mismatch: expected {stock_id}, got {fundamental_data.get('StockID')}")

            logger.info(f"✓ Fetched {stock_id} Q{quarter} {year}")
            return fundamental_data

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {stock_id} Q{quarter} {year}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {stock_id} Q{quarter} {year}: {e}")
            return None

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {stock_id} Q{quarter} {year}: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching {stock_id} Q{quarter} {year}: {e}")
            return None

    def fetch_latest_quarter(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the latest available quarter for a stock

        Tries current quarter first, then previous quarters

        Args:
            stock_id: Stock code

        Returns:
            Latest fundamental data or None
        """
        today = date.today()
        current_year = today.year
        current_quarter = (today.month - 1) // 3 + 1

        # Try current quarter first, then go backwards
        for q_offset in range(4):
            quarter = current_quarter - q_offset
            year = current_year

            # Handle year boundary
            if quarter < 1:
                quarter += 4
                year -= 1

            data = self.fetch_quarterly_data(stock_id, year, quarter)
            if data:
                return data

        logger.warning(f"No recent quarterly data found for {stock_id}")
        return None

    def fetch_multiple_quarters(
        self,
        stock_id: str,
        num_quarters: int = 8,
        end_year: int = None,
        end_quarter: int = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple quarters of data

        Args:
            stock_id: Stock code
            num_quarters: Number of quarters to fetch (default: 8 = 2 years)
            end_year: End year (default: current year)
            end_quarter: End quarter (default: current quarter)

        Returns:
            List of fundamental data dictionaries
        """
        results = []

        # Determine starting point
        if end_year is None or end_quarter is None:
            today = date.today()
            end_year = today.year
            end_quarter = (today.month - 1) // 3 + 1

        # Fetch backwards from end_quarter
        year = end_year
        quarter = end_quarter

        for i in range(num_quarters):
            data = self.fetch_quarterly_data(stock_id, year, quarter)

            if data:
                results.append(data)
            else:
                logger.debug(f"No data for {stock_id} Q{quarter} {year}")

            # Move to previous quarter
            quarter -= 1
            if quarter < 1:
                quarter = 4
                year -= 1

        logger.info(f"Fetched {len(results)}/{num_quarters} quarters for {stock_id}")
        return results

    def fetch_year_data(self, stock_id: str, year: int) -> List[Dict[str, Any]]:
        """
        Fetch all 4 quarters for a given year

        Args:
            stock_id: Stock code
            year: Year to fetch

        Returns:
            List of quarterly data (up to 4 quarters)
        """
        results = []

        for quarter in range(1, 5):
            data = self.fetch_quarterly_data(stock_id, year, quarter)
            if data:
                results.append(data)

        logger.info(f"Fetched {len(results)}/4 quarters for {stock_id} {year}")
        return results

    def fetch_all_stocks_latest(
        self,
        stock_ids: List[str],
        delay: float = 0.5
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch latest quarter data for multiple stocks

        Args:
            stock_ids: List of stock codes
            delay: Delay between requests (seconds)

        Returns:
            Dictionary mapping stock_id to fundamental data
        """
        import time

        results = {}

        for i, stock_id in enumerate(stock_ids):
            logger.info(f"Fetching {i+1}/{len(stock_ids)}: {stock_id}")

            data = self.fetch_latest_quarter(stock_id)
            results[stock_id] = data

            # Rate limiting
            if delay > 0 and i < len(stock_ids) - 1:
                time.sleep(delay)

        successful = sum(1 for v in results.values() if v is not None)
        logger.info(f"Fetched {successful}/{len(stock_ids)} stocks successfully")

        return results

    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw API data to consistent field names

        Args:
            raw_data: Raw data from API

        Returns:
            Normalized dictionary
        """
        return {
            # Identification
            'stock_id': raw_data.get('StockID'),
            'year': raw_data.get('Year'),
            'quarter': raw_data.get('Quarter'),
            'report_date': raw_data.get('Date'),
            'fiscal_year': raw_data.get('FiscalYear'),
            'month_cover': raw_data.get('MonthCover'),

            # Stock Info
            'close_price': raw_data.get('ClosePrice'),
            'par_value': raw_data.get('ParValueA'),
            'shares_outstanding': raw_data.get('PaidupCapShares'),
            'authorized_shares': raw_data.get('Authorized'),

            # Balance Sheet - Assets
            'receivables': raw_data.get('Receivables'),
            'inventories': raw_data.get('Inventories'),
            'current_assets': raw_data.get('CurrentAssets'),
            'fixed_assets': raw_data.get('FixedAssets'),
            'other_assets': raw_data.get('OtherAssets'),
            'total_assets': raw_data.get('TotalAssets'),
            'non_current_assets': raw_data.get('NonCurrentAssets'),

            # Balance Sheet - Liabilities
            'current_liabilities': raw_data.get('CurrentLiabilities'),
            'long_term_liabilities': raw_data.get('LongTermLiabilities'),
            'total_liabilities': raw_data.get('TotalLiabilities'),

            # Balance Sheet - Equity
            'paidup_capital': raw_data.get('PaidupCap'),
            'retained_earnings': raw_data.get('RetainedEarn'),
            'total_equity': raw_data.get('TotalEquity'),
            'minority_interest': raw_data.get('MinInterest'),

            # Income Statement
            'revenue': raw_data.get('TotalSales'),
            'cost_of_goods_sold': raw_data.get('CostGoodSold'),
            'gross_profit': raw_data.get('GrossProfit'),
            'operating_profit': raw_data.get('OperatingProfit'),
            'other_income': raw_data.get('OtherIncome'),
            'earnings_before_tax': raw_data.get('EarningBeforeTax'),
            'tax': raw_data.get('Tax'),
            'net_income': raw_data.get('NetIncome'),

            # Cash Flow
            'cf_operating': raw_data.get('CFOperateActs'),
            'cf_investing': raw_data.get('CFInvestActs'),
            'cf_financing': raw_data.get('CFFinActs'),
            'net_cash_increase': raw_data.get('NetIncreaseCashAndCashEquivalent'),
            'cash_begin': raw_data.get('CashAndCashEquivalentBeginYear'),
            'cash_end': raw_data.get('CashAndCashEquivalentEndYear'),
            'cash_equivalent': raw_data.get('CashAndCashEquivalent'),

            # Pre-calculated Ratios
            'eps': raw_data.get('EPS'),
            'book_value': raw_data.get('BookValue'),
            'pe_ratio': raw_data.get('PriceEarningRatio'),
            'pb_ratio': raw_data.get('PriceBookValue'),
            'debt_equity_ratio': raw_data.get('DebtEquityRatio'),
            'roa_percent': raw_data.get('ROAPercent'),
            'roe_percent': raw_data.get('ROEPercent'),
            'npm_percent': raw_data.get('NPMPercent'),
            'opm_percent': raw_data.get('OPMPercent'),
            'gross_margin_percent': raw_data.get('GrossProfitMarginPercent'),
            'asset_turnover': raw_data.get('TotalAssetsTurnover'),
        }
