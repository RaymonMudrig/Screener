"""
Data validation module for stock screener
Validates price data and detects anomalies
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataValidator:
    """Validate stock price data"""

    def __init__(self):
        self.validation_errors = []

    def validate_price_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a single price record

        Args:
            record: Price record with keys: date, open, high, low, close, volume

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check required fields
        required_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
        for field in required_fields:
            if field not in record:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, errors

        # Validate date format
        try:
            datetime.strptime(record['date'], '%Y-%m-%d')
        except ValueError:
            errors.append(f"Invalid date format: {record['date']} (expected YYYY-MM-DD)")

        # Validate numeric values
        try:
            open_price = float(record['open'])
            high = float(record['high'])
            low = float(record['low'])
            close = float(record['close'])
            volume = int(record['volume'])

            # Check for negative values
            if open_price < 0:
                errors.append(f"Negative open price: {open_price}")
            if high < 0:
                errors.append(f"Negative high price: {high}")
            if low < 0:
                errors.append(f"Negative low price: {low}")
            if close < 0:
                errors.append(f"Negative close price: {close}")
            if volume < 0:
                errors.append(f"Negative volume: {volume}")

            # Check OHLC relationships
            if high < low:
                errors.append(f"High ({high}) is less than Low ({low})")

            if high < open_price:
                errors.append(f"High ({high}) is less than Open ({open_price})")

            if high < close:
                errors.append(f"High ({high}) is less than Close ({close})")

            if low > open_price:
                errors.append(f"Low ({low}) is greater than Open ({open_price})")

            if low > close:
                errors.append(f"Low ({low}) is greater than Close ({close})")

            # Check for zero values (except volume which can be zero)
            if open_price == 0:
                errors.append("Open price is zero")
            if high == 0:
                errors.append("High price is zero")
            if low == 0:
                errors.append("Low price is zero")
            if close == 0:
                errors.append("Close price is zero")

        except (ValueError, TypeError) as e:
            errors.append(f"Invalid numeric value: {e}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_price_data(
        self,
        price_data: List[Dict[str, Any]],
        stock_id: str = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validate a list of price records

        Args:
            price_data: List of price records
            stock_id: Stock ID for logging purposes

        Returns:
            Tuple of (valid_records, invalid_records)
        """
        valid_records = []
        invalid_records = []

        for i, record in enumerate(price_data):
            is_valid, errors = self.validate_price_record(record)

            if is_valid:
                valid_records.append(record)
            else:
                invalid_records.append({
                    'record': record,
                    'errors': errors
                })
                logger.warning(
                    f"Invalid price record for {stock_id or 'unknown'} "
                    f"at index {i}: {', '.join(errors)}"
                )

        if invalid_records:
            logger.warning(
                f"Validation completed for {stock_id or 'unknown'}: "
                f"{len(valid_records)} valid, {len(invalid_records)} invalid"
            )
        else:
            logger.debug(
                f"Validation completed for {stock_id or 'unknown'}: "
                f"all {len(valid_records)} records valid"
            )

        return valid_records, invalid_records

    def detect_outliers(
        self,
        price_data: List[Dict[str, Any]],
        threshold_pct: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Detect outliers in price data (e.g., sudden price jumps)

        Args:
            price_data: List of price records (sorted by date)
            threshold_pct: Percentage threshold for outlier detection

        Returns:
            List of suspected outlier records
        """
        if len(price_data) < 2:
            return []

        outliers = []

        # Sort by date to ensure chronological order
        sorted_data = sorted(price_data, key=lambda x: x['date'])

        for i in range(1, len(sorted_data)):
            prev_close = sorted_data[i - 1]['close']
            curr_open = sorted_data[i]['open']
            curr_close = sorted_data[i]['close']

            # Check for gap between previous close and current open
            if prev_close > 0:
                gap_pct = abs((curr_open - prev_close) / prev_close * 100)
                if gap_pct > threshold_pct:
                    outliers.append({
                        'date': sorted_data[i]['date'],
                        'type': 'gap',
                        'value': gap_pct,
                        'record': sorted_data[i]
                    })
                    logger.info(
                        f"Detected gap outlier on {sorted_data[i]['date']}: "
                        f"{gap_pct:.2f}% gap"
                    )

            # Check for intraday price movement
            if curr_open > 0:
                intraday_pct = abs((curr_close - curr_open) / curr_open * 100)
                if intraday_pct > threshold_pct:
                    outliers.append({
                        'date': sorted_data[i]['date'],
                        'type': 'intraday_movement',
                        'value': intraday_pct,
                        'record': sorted_data[i]
                    })
                    logger.info(
                        f"Detected intraday outlier on {sorted_data[i]['date']}: "
                        f"{intraday_pct:.2f}% movement"
                    )

        return outliers

    def detect_gaps(
        self,
        price_data: List[Dict[str, Any]]
    ) -> List[Tuple[str, str]]:
        """
        Detect date gaps in price data (missing trading days)

        Args:
            price_data: List of price records

        Returns:
            List of tuples (start_date, end_date) representing gaps
        """
        if len(price_data) < 2:
            return []

        # Sort by date
        sorted_data = sorted(price_data, key=lambda x: x['date'])
        gaps = []

        for i in range(1, len(sorted_data)):
            prev_date = datetime.strptime(sorted_data[i - 1]['date'], '%Y-%m-%d')
            curr_date = datetime.strptime(sorted_data[i]['date'], '%Y-%m-%d')

            # Calculate days difference
            days_diff = (curr_date - prev_date).days

            # If gap is more than 7 days (accounting for weekends)
            # this might indicate missing data or market holidays
            if days_diff > 7:
                gaps.append((
                    sorted_data[i - 1]['date'],
                    sorted_data[i]['date']
                ))
                logger.info(
                    f"Detected date gap: {sorted_data[i - 1]['date']} to "
                    f"{sorted_data[i]['date']} ({days_diff} days)"
                )

        return gaps

    def clean_price_data(
        self,
        price_data: List[Dict[str, Any]],
        remove_duplicates: bool = True,
        remove_outliers: bool = False,
        outlier_threshold: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Clean price data by removing duplicates and optionally outliers

        Args:
            price_data: List of price records
            remove_duplicates: Remove duplicate dates
            remove_outliers: Remove detected outliers
            outlier_threshold: Threshold for outlier detection

        Returns:
            Cleaned price data
        """
        cleaned_data = price_data.copy()

        # Remove duplicates
        if remove_duplicates:
            seen_dates = set()
            unique_data = []

            for record in cleaned_data:
                date = record['date']
                if date not in seen_dates:
                    seen_dates.add(date)
                    unique_data.append(record)
                else:
                    logger.warning(f"Removed duplicate record for date: {date}")

            cleaned_data = unique_data
            logger.info(f"Removed {len(price_data) - len(cleaned_data)} duplicate records")

        # Remove outliers
        if remove_outliers:
            outliers = self.detect_outliers(cleaned_data, outlier_threshold)
            outlier_dates = {o['date'] for o in outliers}

            cleaned_data = [
                record for record in cleaned_data
                if record['date'] not in outlier_dates
            ]

            logger.info(f"Removed {len(outliers)} outlier records")

        return cleaned_data

    def get_data_quality_report(
        self,
        price_data: List[Dict[str, Any]],
        stock_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate a data quality report

        Args:
            price_data: List of price records
            stock_id: Stock ID for reporting

        Returns:
            Dictionary with quality metrics
        """
        if not price_data:
            return {
                'stock_id': stock_id,
                'total_records': 0,
                'valid_records': 0,
                'invalid_records': 0,
                'outliers': 0,
                'gaps': 0,
                'quality_score': 0.0
            }

        # Validate all records
        valid_records, invalid_records = self.validate_price_data(price_data, stock_id)

        # Detect outliers
        outliers = self.detect_outliers(valid_records)

        # Detect gaps
        gaps = self.detect_gaps(valid_records)

        # Calculate quality score (0-100)
        total_records = len(price_data)
        valid_pct = len(valid_records) / total_records * 100 if total_records > 0 else 0
        outlier_penalty = (len(outliers) / total_records * 100) if total_records > 0 else 0
        gap_penalty = (len(gaps) / total_records * 100) if total_records > 0 else 0

        quality_score = max(0, valid_pct - outlier_penalty - gap_penalty)

        return {
            'stock_id': stock_id,
            'total_records': total_records,
            'valid_records': len(valid_records),
            'invalid_records': len(invalid_records),
            'outliers': len(outliers),
            'gaps': len(gaps),
            'quality_score': round(quality_score, 2)
        }
