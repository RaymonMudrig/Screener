"""
Trend-following technical indicators
Includes: SMA, EMA, MACD, ADX
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class TrendIndicators:
    """Calculate trend-following indicators"""

    @staticmethod
    def sma(prices: pd.Series, period: int) -> pd.Series:
        """
        Simple Moving Average

        Args:
            prices: Price series (typically close prices)
            period: Number of periods for the average

        Returns:
            SMA series
        """
        return prices.rolling(window=period).mean()

    @staticmethod
    def ema(prices: pd.Series, period: int) -> pd.Series:
        """
        Exponential Moving Average

        Args:
            prices: Price series (typically close prices)
            period: Number of periods for the average

        Returns:
            EMA series
        """
        return prices.ewm(span=period, adjust=False).mean()

    @staticmethod
    def macd(
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence

        Args:
            prices: Price series (typically close prices)
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period

        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        fast_ema = TrendIndicators.ema(prices, fast_period)
        slow_ema = TrendIndicators.ema(prices, slow_period)

        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Average Directional Index (trend strength)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for calculation

        Returns:
            ADX series
        """
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        # Convert to Series
        plus_dm = pd.Series(plus_dm, index=high.index)
        minus_dm = pd.Series(minus_dm, index=high.index)

        # Smooth the values
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx

    @staticmethod
    def parabolic_sar(
        high: pd.Series,
        low: pd.Series,
        acceleration: float = 0.02,
        maximum: float = 0.2
    ) -> pd.Series:
        """
        Parabolic SAR (Stop and Reverse)

        Args:
            high: High prices
            low: Low prices
            acceleration: Acceleration factor
            maximum: Maximum acceleration

        Returns:
            SAR series
        """
        # Initialize
        sar = pd.Series(index=high.index, dtype=float)
        trend = pd.Series(index=high.index, dtype=int)
        af = acceleration
        ep = 0  # Extreme point

        # Start with bullish trend
        sar.iloc[0] = low.iloc[0]
        trend.iloc[0] = 1
        ep = high.iloc[0]

        for i in range(1, len(high)):
            # Calculate SAR
            sar.iloc[i] = sar.iloc[i-1] + af * (ep - sar.iloc[i-1])

            # Check for reversal
            if trend.iloc[i-1] == 1:  # Bullish
                if low.iloc[i] < sar.iloc[i]:
                    # Reverse to bearish
                    trend.iloc[i] = -1
                    sar.iloc[i] = ep
                    ep = low.iloc[i]
                    af = acceleration
                else:
                    trend.iloc[i] = 1
                    if high.iloc[i] > ep:
                        ep = high.iloc[i]
                        af = min(af + acceleration, maximum)
            else:  # Bearish
                if high.iloc[i] > sar.iloc[i]:
                    # Reverse to bullish
                    trend.iloc[i] = 1
                    sar.iloc[i] = ep
                    ep = high.iloc[i]
                    af = acceleration
                else:
                    trend.iloc[i] = -1
                    if low.iloc[i] < ep:
                        ep = low.iloc[i]
                        af = min(af + acceleration, maximum)

        return sar

    @staticmethod
    def calculate_all_trend_indicators(
        df: pd.DataFrame,
        config: Dict = None
    ) -> pd.DataFrame:
        """
        Calculate all trend indicators for a dataframe

        Args:
            df: DataFrame with OHLC data (columns: open, high, low, close, volume)
            config: Configuration dict with indicator parameters

        Returns:
            DataFrame with added indicator columns
        """
        if config is None:
            config = {
                'sma_periods': [20, 50, 200],
                'ema_periods': [12, 26],
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'adx_period': 14
            }

        result = df.copy()

        # Calculate SMAs
        for period in config.get('sma_periods', [20, 50, 200]):
            result[f'sma_{period}'] = TrendIndicators.sma(df['close'], period)

        # Calculate EMAs
        for period in config.get('ema_periods', [12, 26]):
            result[f'ema_{period}'] = TrendIndicators.ema(df['close'], period)

        # Calculate MACD
        macd_line, signal_line, histogram = TrendIndicators.macd(
            df['close'],
            config.get('macd_fast', 12),
            config.get('macd_slow', 26),
            config.get('macd_signal', 9)
        )
        result['macd_line'] = macd_line
        result['macd_signal'] = signal_line
        result['macd_histogram'] = histogram

        # Calculate ADX
        result['adx'] = TrendIndicators.adx(
            df['high'],
            df['low'],
            df['close'],
            config.get('adx_period', 14)
        )

        return result
