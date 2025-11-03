"""
Momentum and oscillator technical indicators
Includes: RSI, Stochastic, Williams %R, CCI, ROC
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class MomentumIndicators:
    """Calculate momentum and oscillator indicators"""

    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index

        Args:
            prices: Price series (typically close prices)
            period: Period for RSI calculation

        Returns:
            RSI series (0-100)
        """
        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            k_period: %K period
            d_period: %D period (signal line)
            smooth_k: Smoothing period for %K

        Returns:
            Tuple of (%K, %D)
        """
        # Calculate raw %K
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        raw_k = 100 * (close - lowest_low) / (highest_high - lowest_low)

        # Smooth %K
        k = raw_k.rolling(window=smooth_k).mean()

        # Calculate %D (signal line)
        d = k.rolling(window=d_period).mean()

        return k, d

    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Williams %R

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for calculation

        Returns:
            Williams %R series (-100 to 0)
        """
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)

        return williams_r

    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """
        Commodity Channel Index

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for calculation

        Returns:
            CCI series
        """
        # Calculate Typical Price
        tp = (high + low + close) / 3

        # Calculate SMA of TP
        sma_tp = tp.rolling(window=period).mean()

        # Calculate Mean Deviation
        mean_dev = tp.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )

        # Calculate CCI
        cci = (tp - sma_tp) / (0.015 * mean_dev)

        return cci

    @staticmethod
    def roc(prices: pd.Series, period: int = 12) -> pd.Series:
        """
        Rate of Change

        Args:
            prices: Price series
            period: Period for calculation

        Returns:
            ROC series (percentage)
        """
        roc = 100 * (prices - prices.shift(period)) / prices.shift(period)
        return roc

    @staticmethod
    def momentum(prices: pd.Series, period: int = 10) -> pd.Series:
        """
        Momentum Indicator

        Args:
            prices: Price series
            period: Period for calculation

        Returns:
            Momentum series
        """
        return prices - prices.shift(period)

    @staticmethod
    def tsi(prices: pd.Series, long_period: int = 25, short_period: int = 13) -> pd.Series:
        """
        True Strength Index

        Args:
            prices: Price series
            long_period: Long smoothing period
            short_period: Short smoothing period

        Returns:
            TSI series
        """
        # Calculate price changes
        price_change = prices.diff()

        # Double smooth price changes
        double_smoothed = price_change.ewm(span=long_period, adjust=False).mean() \
                                      .ewm(span=short_period, adjust=False).mean()

        # Double smooth absolute price changes
        abs_double_smoothed = price_change.abs().ewm(span=long_period, adjust=False).mean() \
                                                .ewm(span=short_period, adjust=False).mean()

        # Calculate TSI
        tsi = 100 * double_smoothed / abs_double_smoothed

        return tsi

    @staticmethod
    def calculate_all_momentum_indicators(
        df: pd.DataFrame,
        config: Dict = None
    ) -> pd.DataFrame:
        """
        Calculate all momentum indicators for a dataframe

        Args:
            df: DataFrame with OHLC data (columns: open, high, low, close, volume)
            config: Configuration dict with indicator parameters

        Returns:
            DataFrame with added indicator columns
        """
        if config is None:
            config = {
                'rsi_period': 14,
                'stochastic_k': 14,
                'stochastic_d': 3,
                'stochastic_smooth': 3,
                'williams_period': 14,
                'cci_period': 20,
                'roc_period': 12
            }

        result = df.copy()

        # Calculate RSI
        result['rsi'] = MomentumIndicators.rsi(
            df['close'],
            config.get('rsi_period', 14)
        )

        # Calculate Stochastic
        stoch_k, stoch_d = MomentumIndicators.stochastic(
            df['high'],
            df['low'],
            df['close'],
            config.get('stochastic_k', 14),
            config.get('stochastic_d', 3),
            config.get('stochastic_smooth', 3)
        )
        result['stoch_k'] = stoch_k
        result['stoch_d'] = stoch_d

        # Calculate Williams %R
        result['williams_r'] = MomentumIndicators.williams_r(
            df['high'],
            df['low'],
            df['close'],
            config.get('williams_period', 14)
        )

        # Calculate CCI
        result['cci'] = MomentumIndicators.cci(
            df['high'],
            df['low'],
            df['close'],
            config.get('cci_period', 20)
        )

        # Calculate ROC
        result['roc'] = MomentumIndicators.roc(
            df['close'],
            config.get('roc_period', 12)
        )

        return result
