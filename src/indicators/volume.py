"""
Volume-based technical indicators
Includes: OBV, Volume SMA, VWAP, Chaikin Money Flow
"""

import pandas as pd
import numpy as np
from typing import Dict


class VolumeIndicators:
    """Calculate volume-based indicators"""

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On Balance Volume

        Args:
            close: Close prices
            volume: Volume

        Returns:
            OBV series
        """
        # Determine direction: 1 if close > previous close, -1 otherwise
        direction = np.where(close > close.shift(1), 1,
                           np.where(close < close.shift(1), -1, 0))

        # Calculate OBV
        obv = (direction * volume).cumsum()

        return pd.Series(obv, index=close.index)

    @staticmethod
    def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
        """
        Volume Simple Moving Average

        Args:
            volume: Volume series
            period: Period for average

        Returns:
            Volume SMA series
        """
        return volume.rolling(window=period).mean()

    @staticmethod
    def volume_roc(volume: pd.Series, period: int = 12) -> pd.Series:
        """
        Volume Rate of Change

        Args:
            volume: Volume series
            period: Period for calculation

        Returns:
            Volume ROC series (percentage)
        """
        roc = 100 * (volume - volume.shift(period)) / volume.shift(period)
        return roc

    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Volume Weighted Average Price

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume

        Returns:
            VWAP series
        """
        # Calculate typical price
        typical_price = (high + low + close) / 3

        # Calculate VWAP
        vwap = (typical_price * volume).cumsum() / volume.cumsum()

        return vwap

    @staticmethod
    def chaikin_money_flow(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = 20
    ) -> pd.Series:
        """
        Chaikin Money Flow

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume
            period: Period for calculation

        Returns:
            CMF series
        """
        # Calculate Money Flow Multiplier
        mf_multiplier = ((close - low) - (high - close)) / (high - low)

        # Handle division by zero
        mf_multiplier = mf_multiplier.fillna(0)

        # Calculate Money Flow Volume
        mf_volume = mf_multiplier * volume

        # Calculate CMF
        cmf = mf_volume.rolling(window=period).sum() / volume.rolling(window=period).sum()

        return cmf

    @staticmethod
    def accumulation_distribution(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series
    ) -> pd.Series:
        """
        Accumulation/Distribution Line

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume

        Returns:
            A/D Line series
        """
        # Calculate Money Flow Multiplier
        mf_multiplier = ((close - low) - (high - close)) / (high - low)

        # Handle division by zero
        mf_multiplier = mf_multiplier.fillna(0)

        # Calculate Money Flow Volume
        mf_volume = mf_multiplier * volume

        # Calculate cumulative A/D Line
        ad_line = mf_volume.cumsum()

        return ad_line

    @staticmethod
    def money_flow_index(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Money Flow Index (volume-weighted RSI)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume
            period: Period for calculation

        Returns:
            MFI series (0-100)
        """
        # Calculate Typical Price
        typical_price = (high + low + close) / 3

        # Calculate Raw Money Flow
        raw_money_flow = typical_price * volume

        # Separate positive and negative money flow
        positive_flow = pd.Series(0.0, index=close.index)
        negative_flow = pd.Series(0.0, index=close.index)

        for i in range(1, len(typical_price)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                positive_flow.iloc[i] = raw_money_flow.iloc[i]
            elif typical_price.iloc[i] < typical_price.iloc[i-1]:
                negative_flow.iloc[i] = raw_money_flow.iloc[i]

        # Calculate Money Flow Ratio
        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()

        mfr = positive_mf / negative_mf

        # Calculate MFI
        mfi = 100 - (100 / (1 + mfr))

        return mfi

    @staticmethod
    def volume_price_trend(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Volume Price Trend

        Args:
            close: Close prices
            volume: Volume

        Returns:
            VPT series
        """
        # Calculate price change percentage
        price_change_pct = close.pct_change()

        # Calculate VPT
        vpt = (price_change_pct * volume).cumsum()

        return vpt

    @staticmethod
    def calculate_all_volume_indicators(
        df: pd.DataFrame,
        config: Dict = None
    ) -> pd.DataFrame:
        """
        Calculate all volume indicators for a dataframe

        Args:
            df: DataFrame with OHLC data (columns: open, high, low, close, volume)
            config: Configuration dict with indicator parameters

        Returns:
            DataFrame with added indicator columns
        """
        if config is None:
            config = {
                'volume_sma_period': 20,
                'cmf_period': 20,
                'mfi_period': 14
            }

        result = df.copy()

        # Calculate OBV
        result['obv'] = VolumeIndicators.obv(df['close'], df['volume'])

        # Calculate Volume SMA
        result['volume_sma'] = VolumeIndicators.volume_sma(
            df['volume'],
            config.get('volume_sma_period', 20)
        )

        # Calculate Volume ROC
        result['volume_roc'] = VolumeIndicators.volume_roc(df['volume'])

        # Calculate VWAP
        result['vwap'] = VolumeIndicators.vwap(
            df['high'],
            df['low'],
            df['close'],
            df['volume']
        )

        # Calculate Chaikin Money Flow
        result['cmf'] = VolumeIndicators.chaikin_money_flow(
            df['high'],
            df['low'],
            df['close'],
            df['volume'],
            config.get('cmf_period', 20)
        )

        # Calculate Accumulation/Distribution
        result['ad_line'] = VolumeIndicators.accumulation_distribution(
            df['high'],
            df['low'],
            df['close'],
            df['volume']
        )

        # Calculate Money Flow Index
        result['mfi'] = VolumeIndicators.money_flow_index(
            df['high'],
            df['low'],
            df['close'],
            df['volume'],
            config.get('mfi_period', 14)
        )

        # Calculate Volume Price Trend
        result['vpt'] = VolumeIndicators.volume_price_trend(
            df['close'],
            df['volume']
        )

        return result
