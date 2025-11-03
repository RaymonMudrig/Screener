"""
Data fetching module for stock screener
Fetches stock list and price data from IDX sources
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from urllib3.exceptions import InsecureRequestWarning

from ..utils.logger import get_logger
from ..utils.config import get_config

# Suppress SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_logger(__name__)


class DataFetcher:
    """Fetch stock data from IDX sources"""

    def __init__(self):
        self.config = get_config()
        self.stock_list_url = self.config.get('data_sources.stock_list_url')
        self.price_data_url = self.config.get('data_sources.price_data_url')
        self.verify_ssl = self.config.get('data_sources.verify_ssl', False)
        self.timeout = self.config.get('data_sources.timeout', 30)
        self.retry_attempts = self.config.get('data_sources.retry_attempts', 3)
        self.retry_delay = self.config.get('data_sources.retry_delay', 5)

    def _make_request(self, url: str, params: Dict = None) -> Optional[Any]:
        """
        Make HTTP request with retry logic

        Args:
            url: URL to fetch
            params: Query parameters

        Returns:
            Response data or None if failed
        """
        for attempt in range(self.retry_attempts):
            try:
                logger.debug(f"Fetching URL: {url} (attempt {attempt + 1}/{self.retry_attempts})")

                response = requests.get(
                    url,
                    params=params,
                    verify=self.verify_ssl,
                    timeout=self.timeout
                )

                response.raise_for_status()

                # Try to parse JSON
                try:
                    return response.json()
                except ValueError:
                    # If not JSON, return text
                    return response.text

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.retry_attempts}): {e}")

                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to fetch {url} after {self.retry_attempts} attempts")
                    return None

        return None

    def fetch_stock_list(self) -> List[Dict[str, Any]]:
        """
        Fetch list of all stocks from IDX

        Returns:
            List of stock dictionaries with keys: stock_id, stock_code, stock_name, sector, subsector
        """
        logger.info("Fetching stock list from IDX")

        data = self._make_request(self.stock_list_url)

        if data is None:
            logger.error("Failed to fetch stock list")
            return []

        # Debug: log the type and preview of data
        logger.debug(f"Response type: {type(data)}")
        if isinstance(data, str):
            logger.debug(f"Response preview: {data[:200]}")

        # Parse the response based on actual API format
        # Note: Actual format may vary, adjust parsing as needed
        stocks = []

        try:
            # Handle string response (might be HTML or non-JSON)
            if isinstance(data, str):
                logger.error(f"API returned string instead of JSON. Preview: {data[:200]}")
                return []

            # IDX API returns list of pipe-delimited strings
            # Format: "STOCKCODE|Stock Name|BoardType|...other fields..."
            # STOCKCODE formats:
            #   - "SYMBOL" = Regular Market (what we want!)
            #   - "SYMBOL-TN" = Cash Market (Tunai)
            #   - "SYMBOL-NG" = Negotiated Market
            if isinstance(data, list):
                for item in data:
                    # Parse pipe-delimited string
                    if isinstance(item, str):
                        parts = item.split('|')
                        if len(parts) >= 2:
                            stock_code = parts[0].strip()
                            stock_name = parts[1].strip() if len(parts) > 1 else ''
                            board_type = parts[2].strip() if len(parts) > 2 else ''

                            # Skip if empty code
                            if not stock_code:
                                continue

                            # Only accept Regular Market stocks (no suffix)
                            # Skip TN (Cash Market) and NG (Negotiated Market)
                            if '-TN' in stock_code or '-NG' in stock_code:
                                logger.debug(f"Skipping non-regular market: {stock_code}")
                                continue

                            stock = {
                                'stock_id': stock_code,
                                'stock_code': stock_code,
                                'stock_name': stock_name,
                                'sector': '',  # Not available in this API
                                'subsector': ''  # Not available in this API
                            }

                            # Avoid duplicates
                            if not any(s['stock_id'] == stock_code for s in stocks):
                                stocks.append(stock)
                                logger.debug(f"Added stock: {stock_code} - {stock_name}")

                    # Fallback: Handle if format changes to dict
                    elif isinstance(item, dict):
                        stock = {
                            'stock_id': item.get('StockCode', item.get('stockCode', '')),
                            'stock_code': item.get('StockCode', item.get('stockCode', '')),
                            'stock_name': item.get('StockName', item.get('stockName', '')),
                            'sector': item.get('Sector', item.get('sector', '')),
                            'subsector': item.get('SubSector', item.get('subsector', ''))
                        }
                        stocks.append(stock)

            elif isinstance(data, dict):
                # If response is wrapped in a dict
                stock_data = data.get('data', data.get('stocks', []))
                for item in stock_data:
                    if isinstance(item, str):
                        # Parse pipe-delimited string
                        parts = item.split('|')
                        if len(parts) >= 2:
                            stock_code = parts[0].strip()
                            stock_name = parts[1].strip()

                            # Only accept Regular Market (no suffix)
                            if '-TN' in stock_code or '-NG' in stock_code:
                                continue

                            stock = {
                                'stock_id': stock_code,
                                'stock_code': stock_code,
                                'stock_name': stock_name,
                                'sector': '',
                                'subsector': ''
                            }
                            if not any(s['stock_id'] == stock_code for s in stocks):
                                stocks.append(stock)
                    elif isinstance(item, dict):
                        stock = {
                            'stock_id': item.get('StockCode', item.get('stockCode', '')),
                            'stock_code': item.get('StockCode', item.get('stockCode', '')),
                            'stock_name': item.get('StockName', item.get('stockName', '')),
                            'sector': item.get('Sector', item.get('sector', '')),
                            'subsector': item.get('SubSector', item.get('subsector', ''))
                        }
                        stocks.append(stock)

            logger.info(f"Successfully fetched {len(stocks)} stocks")
            return stocks

        except Exception as e:
            logger.error(f"Error parsing stock list: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def fetch_price_data(
        self,
        stock_id: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch price data for a specific stock

        Args:
            stock_id: Stock code
            start_date: Start date for price data
            end_date: End date for price data

        Returns:
            List of price dictionaries with keys: date, open, high, low, close, volume
        """
        # Default to last year if no dates provided
        if end_date is None:
            end_date = datetime.now()

        if start_date is None:
            start_date = end_date - timedelta(days=365)

        # Format dates as m/d/yyyy (without leading zeros)
        start_str = f"{start_date.month}/{start_date.day}/{start_date.year}"
        end_str = f"{end_date.month}/{end_date.day}/{end_date.year}"

        # Construct URL
        url = f"{self.price_data_url}?stockID={stock_id}&code={start_str}-{end_str}"

        logger.debug(f"Fetching price data for {stock_id} from {start_str} to {end_str}")

        data = self._make_request(url)

        if data is None:
            logger.warning(f"Failed to fetch price data for {stock_id}")
            return []

        # Parse the response
        price_data = []

        try:
            # Parse based on actual API response format
            # Assuming response is a list of price records
            if isinstance(data, list):
                for item in data:
                    price = self._parse_price_record(item)
                    if price:
                        price_data.append(price)

            elif isinstance(data, dict):
                # If response is wrapped in a dict
                records = data.get('data', data.get('prices', []))
                for item in records:
                    price = self._parse_price_record(item)
                    if price:
                        price_data.append(price)

            logger.info(f"Fetched {len(price_data)} price records for {stock_id}")
            return price_data

        except Exception as e:
            logger.error(f"Error parsing price data for {stock_id}: {e}")
            return []

    def _parse_price_record(self, item: Dict) -> Optional[Dict[str, Any]]:
        """
        Parse a single price record from API response

        Args:
            item: Price record from API

        Returns:
            Normalized price dictionary or None if invalid
        """
        try:
            # Try different possible field names
            # IDX API uses 'Stamp' field with ISO datetime format
            date_str = item.get('Stamp', item.get('Date', item.get('date', item.get('tradeDate', ''))))
            open_price = float(item.get('Open', item.get('open', item.get('openPrice', 0))))
            high = float(item.get('High', item.get('high', item.get('highPrice', 0))))
            low = float(item.get('Low', item.get('low', item.get('lowPrice', 0))))
            close = float(item.get('Close', item.get('close', item.get('closePrice', 0))))
            volume = int(item.get('Volume', item.get('volume', item.get('tradeVolume', 0))))

            # Parse date to standard format (YYYY-MM-DD)
            if date_str:
                # Handle various date formats
                try:
                    # Try parsing common formats, including ISO datetime
                    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            date_str = parsed_date.strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue
                except Exception:
                    logger.warning(f"Could not parse date: {date_str}")
                    return None

            return {
                'date': date_str,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            }

        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid price record: {e}")
            return None

    def fetch_price_data_bulk(
        self,
        stock_ids: List[str],
        start_date: datetime = None,
        end_date: datetime = None,
        delay: float = 1.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch price data for multiple stocks

        Args:
            stock_ids: List of stock codes
            start_date: Start date for price data
            end_date: End date for price data
            delay: Delay between requests in seconds (to avoid rate limiting)

        Returns:
            Dictionary mapping stock_id to list of price records
        """
        logger.info(f"Fetching price data for {len(stock_ids)} stocks")

        results = {}

        for i, stock_id in enumerate(stock_ids):
            logger.info(f"Fetching {i+1}/{len(stock_ids)}: {stock_id}")

            price_data = self.fetch_price_data(stock_id, start_date, end_date)
            results[stock_id] = price_data

            # Delay to avoid overwhelming the server
            if i < len(stock_ids) - 1:
                time.sleep(delay)

        logger.info(f"Bulk fetch completed. Fetched data for {len(results)} stocks")
        return results

    def fetch_latest_price_data(
        self,
        stock_id: str,
        last_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch only new price data since last update

        Args:
            stock_id: Stock code
            last_date: Last date we have data for (YYYY-MM-DD format)

        Returns:
            List of new price records
        """
        if last_date:
            # Parse last_date and add one day
            try:
                last_datetime = datetime.strptime(last_date, '%Y-%m-%d')
                start_date = last_datetime + timedelta(days=1)
            except ValueError:
                logger.warning(f"Invalid last_date format: {last_date}, fetching all data")
                start_date = None
        else:
            start_date = None

        return self.fetch_price_data(stock_id, start_date=start_date)
