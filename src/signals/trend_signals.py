"""
Trend-based signal detectors
Golden Cross, Death Cross, MACD crossovers, etc.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any

from .detector import BaseSignalDetector, Signal, SignalType, SignalDirection
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TrendSignalDetector(BaseSignalDetector):
    """Detect trend-based trading signals"""

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """Detect all trend signals"""
        signals = []

        # Need at least 2 rows for crossover detection
        if len(df) < 2:
            return signals

        # Detect signals only for the latest date
        latest_index = len(df) - 1
        latest_date = df.index[latest_index].strftime('%Y-%m-%d')
        latest_price = df['close'].iloc[latest_index]

        # Golden Cross / Death Cross
        if 'sma_50' in df.columns and 'sma_200' in df.columns:
            golden_cross = self.detect_golden_cross(df, latest_index, latest_date, latest_price)
            if golden_cross:
                signals.append(golden_cross)

            death_cross = self.detect_death_cross(df, latest_index, latest_date, latest_price)
            if death_cross:
                signals.append(death_cross)

        # Fast Cross (SMA 20/50)
        if 'sma_20' in df.columns and 'sma_50' in df.columns:
            fast_cross = self.detect_fast_cross(df, latest_index, latest_date, latest_price)
            if fast_cross:
                signals.append(fast_cross)

        # MACD Crossover
        if 'macd_line' in df.columns and 'macd_signal' in df.columns:
            macd_signal = self.detect_macd_crossover(df, latest_index, latest_date, latest_price)
            if macd_signal:
                signals.append(macd_signal)

        # MACD Histogram Reversal
        if 'macd_histogram' in df.columns:
            histogram_signal = self.detect_macd_histogram_reversal(df, latest_index, latest_date, latest_price)
            if histogram_signal:
                signals.append(histogram_signal)

        # Moving Average Slope Change
        if 'sma_50' in df.columns:
            slope_signal = self.detect_ma_slope_change(df, latest_index, latest_date, latest_price)
            if slope_signal:
                signals.append(slope_signal)

        return signals

    def detect_golden_cross(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect Golden Cross (SMA 50 crosses above SMA 200)"""
        if self.is_crossover(df['sma_50'], df['sma_200'], index):
            # Base strength: 60 (strong bullish signal)
            base_strength = 60.0

            # Check confirmations
            volume_conf = self.get_volume_confirmation(df, index)

            # Check ADX for trend strength
            trend_strong = False
            if 'adx' in df.columns and not pd.isna(df['adx'].iloc[index]):
                trend_strong = df['adx'].iloc[index] > 25

            strength = self.calculate_strength(
                base_strength,
                volume_confirmed=volume_conf,
                trend_aligned=trend_strong,
                multiple_indicators=0
            )

            return Signal(
                signal_name="Golden Cross",
                signal_type=SignalType.TREND,
                direction=SignalDirection.BULLISH,
                strength=strength,
                date=date,
                price=price,
                metadata={
                    'sma_50': float(df['sma_50'].iloc[index]),
                    'sma_200': float(df['sma_200'].iloc[index]),
                    'volume_confirmed': volume_conf,
                    'trend_strong': trend_strong
                }
            )

        return None

    def detect_death_cross(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect Death Cross (SMA 50 crosses below SMA 200)"""
        if self.is_crossunder(df['sma_50'], df['sma_200'], index):
            base_strength = 60.0

            volume_conf = self.get_volume_confirmation(df, index)
            trend_strong = False
            if 'adx' in df.columns and not pd.isna(df['adx'].iloc[index]):
                trend_strong = df['adx'].iloc[index] > 25

            strength = self.calculate_strength(
                base_strength,
                volume_confirmed=volume_conf,
                trend_aligned=trend_strong,
                multiple_indicators=0
            )

            return Signal(
                signal_name="Death Cross",
                signal_type=SignalType.TREND,
                direction=SignalDirection.BEARISH,
                strength=strength,
                date=date,
                price=price,
                metadata={
                    'sma_50': float(df['sma_50'].iloc[index]),
                    'sma_200': float(df['sma_200'].iloc[index]),
                    'volume_confirmed': volume_conf,
                    'trend_strong': trend_strong
                }
            )

        return None

    def detect_fast_cross(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect Fast Cross (SMA 20 crosses SMA 50)"""
        # Bullish fast cross
        if self.is_crossover(df['sma_20'], df['sma_50'], index):
            base_strength = 50.0
            volume_conf = self.get_volume_confirmation(df, index)
            trend_aligned = self.get_trend_alignment(df, index, bullish=True)

            strength = self.calculate_strength(
                base_strength,
                volume_confirmed=volume_conf,
                trend_aligned=trend_aligned
            )

            return Signal(
                signal_name="Fast Cross Bullish",
                signal_type=SignalType.TREND,
                direction=SignalDirection.BULLISH,
                strength=strength,
                date=date,
                price=price,
                metadata={
                    'sma_20': float(df['sma_20'].iloc[index]),
                    'sma_50': float(df['sma_50'].iloc[index])
                }
            )

        # Bearish fast cross
        if self.is_crossunder(df['sma_20'], df['sma_50'], index):
            base_strength = 50.0
            volume_conf = self.get_volume_confirmation(df, index)
            trend_aligned = self.get_trend_alignment(df, index, bullish=False)

            strength = self.calculate_strength(
                base_strength,
                volume_confirmed=volume_conf,
                trend_aligned=trend_aligned
            )

            return Signal(
                signal_name="Fast Cross Bearish",
                signal_type=SignalType.TREND,
                direction=SignalDirection.BEARISH,
                strength=strength,
                date=date,
                price=price,
                metadata={
                    'sma_20': float(df['sma_20'].iloc[index]),
                    'sma_50': float(df['sma_50'].iloc[index])
                }
            )

        return None

    def detect_macd_crossover(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect MACD line crossing signal line"""
        # Bullish crossover
        if self.is_crossover(df['macd_line'], df['macd_signal'], index):
            base_strength = 55.0
            volume_conf = self.get_volume_confirmation(df, index)
            trend_aligned = self.get_trend_alignment(df, index, bullish=True)

            # Stronger if MACD is above zero
            above_zero = df['macd_line'].iloc[index] > 0

            strength = self.calculate_strength(
                base_strength,
                volume_confirmed=volume_conf,
                trend_aligned=trend_aligned,
                multiple_indicators=1 if above_zero else 0
            )

            return Signal(
                signal_name="MACD Bullish Crossover",
                signal_type=SignalType.TREND,
                direction=SignalDirection.BULLISH,
                strength=strength,
                date=date,
                price=price,
                metadata={
                    'macd_line': float(df['macd_line'].iloc[index]),
                    'macd_signal': float(df['macd_signal'].iloc[index]),
                    'above_zero': above_zero
                }
            )

        # Bearish crossover
        if self.is_crossunder(df['macd_line'], df['macd_signal'], index):
            base_strength = 55.0
            volume_conf = self.get_volume_confirmation(df, index)
            trend_aligned = self.get_trend_alignment(df, index, bullish=False)

            below_zero = df['macd_line'].iloc[index] < 0

            strength = self.calculate_strength(
                base_strength,
                volume_confirmed=volume_conf,
                trend_aligned=trend_aligned,
                multiple_indicators=1 if below_zero else 0
            )

            return Signal(
                signal_name="MACD Bearish Crossover",
                signal_type=SignalType.TREND,
                direction=SignalDirection.BEARISH,
                strength=strength,
                date=date,
                price=price,
                metadata={
                    'macd_line': float(df['macd_line'].iloc[index]),
                    'macd_signal': float(df['macd_signal'].iloc[index]),
                    'below_zero': below_zero
                }
            )

        return None

    def detect_macd_histogram_reversal(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect MACD histogram changing direction"""
        if index < 2:
            return None

        current = df['macd_histogram'].iloc[index]
        previous = df['macd_histogram'].iloc[index-1]
        before = df['macd_histogram'].iloc[index-2]

        # Bullish reversal: was decreasing, now increasing
        if before > previous and previous < 0 and current > previous:
            base_strength = 45.0
            volume_conf = self.get_volume_confirmation(df, index)

            strength = self.calculate_strength(
                base_strength,
                volume_confirmed=volume_conf
            )

            return Signal(
                signal_name="MACD Histogram Bullish Reversal",
                signal_type=SignalType.TREND,
                direction=SignalDirection.BULLISH,
                strength=strength,
                date=date,
                price=price,
                metadata={'histogram': float(current)}
            )

        # Bearish reversal: was increasing, now decreasing
        if before < previous and previous > 0 and current < previous:
            base_strength = 45.0
            volume_conf = self.get_volume_confirmation(df, index)

            strength = self.calculate_strength(
                base_strength,
                volume_confirmed=volume_conf
            )

            return Signal(
                signal_name="MACD Histogram Bearish Reversal",
                signal_type=SignalType.TREND,
                direction=SignalDirection.BEARISH,
                strength=strength,
                date=date,
                price=price,
                metadata={'histogram': float(current)}
            )

        return None

    def detect_ma_slope_change(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect significant change in moving average slope"""
        if index < 5:
            return None

        # Calculate slope of SMA50 over last 5 days
        sma = df['sma_50'].iloc[index-5:index+1]
        if sma.isna().any():
            return None

        # Linear regression slope
        x = np.arange(len(sma))
        slope = np.polyfit(x, sma, 1)[0]

        # Previous slope
        sma_prev = df['sma_50'].iloc[index-6:index]
        slope_prev = np.polyfit(np.arange(len(sma_prev)), sma_prev, 1)[0]

        # Detect acceleration (slope change)
        if slope > 0 and slope > slope_prev * 1.5:  # Accelerating upward
            return Signal(
                signal_name="MA Uptrend Acceleration",
                signal_type=SignalType.TREND,
                direction=SignalDirection.BULLISH,
                strength=40.0,
                date=date,
                price=price,
                metadata={'slope': float(slope), 'slope_prev': float(slope_prev)}
            )

        if slope < 0 and slope < slope_prev * 1.5:  # Accelerating downward
            return Signal(
                signal_name="MA Downtrend Acceleration",
                signal_type=SignalType.TREND,
                direction=SignalDirection.BEARISH,
                strength=40.0,
                date=date,
                price=price,
                metadata={'slope': float(slope), 'slope_prev': float(slope_prev)}
            )

        return None
