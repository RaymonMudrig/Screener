"""
Signal Detection Base Classes
Provides base functionality for all signal detectors
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger(__name__)


class SignalType(Enum):
    """Signal type categories"""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    PATTERN = "pattern"


class SignalDirection(Enum):
    """Signal direction"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class Signal:
    """Represents a detected trading signal"""

    def __init__(
        self,
        signal_name: str,
        signal_type: SignalType,
        direction: SignalDirection,
        strength: float,
        date: str,
        price: float = None,
        metadata: Dict[str, Any] = None
    ):
        self.signal_name = signal_name
        self.signal_type = signal_type
        self.direction = direction
        self.strength = strength  # 0-100
        self.date = date
        self.price = price
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary"""
        return {
            'signal_name': self.signal_name,
            'signal_type': self.signal_type.value,
            'direction': self.direction.value,
            'strength': self.strength,
            'date': self.date,
            'price': self.price,
            'metadata': self.metadata
        }

    def __repr__(self):
        return f"Signal({self.signal_name}, {self.direction.value}, strength={self.strength:.1f})"


class BaseSignalDetector:
    """Base class for signal detectors"""

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """
        Detect signals in the given dataframe

        Args:
            df: DataFrame with OHLCV and indicator data

        Returns:
            List of detected signals
        """
        raise NotImplementedError("Subclasses must implement detect()")

    def calculate_strength(
        self,
        base_strength: float,
        volume_confirmed: bool = False,
        trend_aligned: bool = False,
        multiple_indicators: int = 0
    ) -> float:
        """
        Calculate signal strength with confirmation factors

        Args:
            base_strength: Base strength (0-100)
            volume_confirmed: Volume confirms the signal
            trend_aligned: Trend aligns with signal
            multiple_indicators: Number of additional confirming indicators

        Returns:
            Adjusted strength (0-100)
        """
        strength = base_strength

        # Volume confirmation adds up to 20 points
        if volume_confirmed:
            strength += 20

        # Trend alignment adds up to 15 points
        if trend_aligned:
            strength += 15

        # Multiple indicator confirmation adds 10 points each (max 30)
        strength += min(multiple_indicators * 10, 30)

        # Cap at 100
        return min(strength, 100.0)

    def is_crossover(self, series1: pd.Series, series2: pd.Series, index: int) -> bool:
        """
        Check if series1 crosses above series2 at the given index

        Args:
            series1: First series
            series2: Second series
            index: Index to check

        Returns:
            True if crossover detected
        """
        if index < 1:
            return False

        # Previous: series1 < series2, Current: series1 > series2
        return (series1.iloc[index-1] < series2.iloc[index-1] and
                series1.iloc[index] > series2.iloc[index])

    def is_crossunder(self, series1: pd.Series, series2: pd.Series, index: int) -> bool:
        """
        Check if series1 crosses below series2 at the given index

        Args:
            series1: First series
            series2: Second series
            index: Index to check

        Returns:
            True if crossunder detected
        """
        if index < 1:
            return False

        # Previous: series1 > series2, Current: series1 < series2
        return (series1.iloc[index-1] > series2.iloc[index-1] and
                series1.iloc[index] < series2.iloc[index])

    def get_volume_confirmation(self, df: pd.DataFrame, index: int) -> bool:
        """
        Check if volume confirms the signal

        Args:
            df: DataFrame with volume data
            index: Index to check

        Returns:
            True if volume is above average
        """
        if 'volume_sma' not in df.columns:
            return False

        current_volume = df['volume'].iloc[index]
        avg_volume = df['volume_sma'].iloc[index]

        # Volume is significant if > 1.5x average
        return current_volume > (avg_volume * 1.5)

    def get_trend_alignment(self, df: pd.DataFrame, index: int, bullish: bool) -> bool:
        """
        Check if trend aligns with signal direction

        Args:
            df: DataFrame with trend indicators
            index: Index to check
            bullish: True for bullish signal, False for bearish

        Returns:
            True if trend aligns
        """
        if 'sma_50' not in df.columns or 'sma_200' not in df.columns:
            return False

        sma50 = df['sma_50'].iloc[index]
        sma200 = df['sma_200'].iloc[index]

        if pd.isna(sma50) or pd.isna(sma200):
            return False

        # Bullish: SMA50 > SMA200, Bearish: SMA50 < SMA200
        if bullish:
            return sma50 > sma200
        else:
            return sma50 < sma200
