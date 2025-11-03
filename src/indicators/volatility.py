"""
Volatility technical indicators
Includes: Bollinger Bands, ATR, Bollinger Band Width, %B
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class VolatilityIndicators:
    """Calculate volatility indicators"""

    @staticmethod
    def bollinger_bands(
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands

        Args:
            prices: Price series (typically close prices)
            period: Period for moving average
            std_dev: Number of standard deviations

        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        middle_band = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        return upper_band, middle_band, lower_band

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Average True Range

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for ATR calculation

        Returns:
            ATR series
        """
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR (smoothed TR)
        atr = tr.rolling(window=period).mean()

        return atr

    @staticmethod
    def bollinger_band_width(
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.Series:
        """
        Bollinger Band Width (measure of volatility)

        Args:
            prices: Price series
            period: Period for calculation
            std_dev: Number of standard deviations

        Returns:
            Band width series
        """
        upper, middle, lower = VolatilityIndicators.bollinger_bands(prices, period, std_dev)

        # Width = (Upper - Lower) / Middle
        width = (upper - lower) / middle

        return width

    @staticmethod
    def percent_b(
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.Series:
        """
        %B Indicator (position within Bollinger Bands)

        Args:
            prices: Price series
            period: Period for calculation
            std_dev: Number of standard deviations

        Returns:
            %B series (0-1, can go beyond)
        """
        upper, middle, lower = VolatilityIndicators.bollinger_bands(prices, period, std_dev)

        # %B = (Price - Lower) / (Upper - Lower)
        percent_b = (prices - lower) / (upper - lower)

        return percent_b

    @staticmethod
    def keltner_channels(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 20,
        atr_mult: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Keltner Channels

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for calculation
            atr_mult: ATR multiplier for channel width

        Returns:
            Tuple of (upper_channel, middle_line, lower_channel)
        """
        # Middle line is EMA of close
        middle = close.ewm(span=period, adjust=False).mean()

        # Calculate ATR
        atr = VolatilityIndicators.atr(high, low, close, period)

        # Channels
        upper = middle + (atr * atr_mult)
        lower = middle - (atr * atr_mult)

        return upper, middle, lower

    @staticmethod
    def donchian_channel(
        high: pd.Series,
        low: pd.Series,
        period: int = 20
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Donchian Channel

        Args:
            high: High prices
            low: Low prices
            period: Period for calculation

        Returns:
            Tuple of (upper_channel, middle_line, lower_channel)
        """
        upper = high.rolling(window=period).max()
        lower = low.rolling(window=period).min()
        middle = (upper + lower) / 2

        return upper, middle, lower

    @staticmethod
    def historical_volatility(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Historical Volatility (annualized)

        Args:
            prices: Price series
            period: Period for calculation

        Returns:
            Historical volatility series (percentage)
        """
        # Calculate log returns
        log_returns = np.log(prices / prices.shift(1))

        # Calculate standard deviation of returns
        volatility = log_returns.rolling(window=period).std()

        # Annualize (assuming 252 trading days)
        annualized_vol = volatility * np.sqrt(252) * 100

        return annualized_vol

    @staticmethod
    def calculate_all_volatility_indicators(
        df: pd.DataFrame,
        config: Dict = None
    ) -> pd.DataFrame:
        """
        Calculate all volatility indicators for a dataframe

        Args:
            df: DataFrame with OHLC data (columns: open, high, low, close, volume)
            config: Configuration dict with indicator parameters

        Returns:
            DataFrame with added indicator columns
        """
        if config is None:
            config = {
                'bollinger_period': 20,
                'bollinger_std': 2.0,
                'atr_period': 14
            }

        result = df.copy()

        # Calculate Bollinger Bands
        bb_upper, bb_middle, bb_lower = VolatilityIndicators.bollinger_bands(
            df['close'],
            config.get('bollinger_period', 20),
            config.get('bollinger_std', 2.0)
        )
        result['bb_upper'] = bb_upper
        result['bb_middle'] = bb_middle
        result['bb_lower'] = bb_lower

        # Calculate Bollinger Band Width
        result['bb_width'] = VolatilityIndicators.bollinger_band_width(
            df['close'],
            config.get('bollinger_period', 20),
            config.get('bollinger_std', 2.0)
        )

        # Calculate %B
        result['percent_b'] = VolatilityIndicators.percent_b(
            df['close'],
            config.get('bollinger_period', 20),
            config.get('bollinger_std', 2.0)
        )

        # Calculate ATR
        result['atr'] = VolatilityIndicators.atr(
            df['high'],
            df['low'],
            df['close'],
            config.get('atr_period', 14)
        )

        # Calculate Historical Volatility
        result['hist_volatility'] = VolatilityIndicators.historical_volatility(
            df['close'],
            config.get('bollinger_period', 20)
        )

        return result
