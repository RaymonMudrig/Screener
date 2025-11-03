"""
Momentum-based signal detectors
RSI extremes, Stochastic crossovers, Divergences, etc.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any

from .detector import BaseSignalDetector, Signal, SignalType, SignalDirection
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MomentumSignalDetector(BaseSignalDetector):
    """Detect momentum-based trading signals"""

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.rsi_oversold = config.get('rsi_oversold', 30) if config else 30
        self.rsi_overbought = config.get('rsi_overbought', 70) if config else 70

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """Detect all momentum signals"""
        signals = []

        if len(df) < 2:
            return signals

        latest_index = len(df) - 1
        latest_date = df.index[latest_index].strftime('%Y-%m-%d')
        latest_price = df['close'].iloc[latest_index]

        # RSI Signals
        if 'rsi' in df.columns:
            rsi_signals = self.detect_rsi_signals(df, latest_index, latest_date, latest_price)
            signals.extend(rsi_signals)

        # Stochastic Signals
        if 'stoch_k' in df.columns and 'stoch_d' in df.columns:
            stoch_signal = self.detect_stochastic_crossover(df, latest_index, latest_date, latest_price)
            if stoch_signal:
                signals.append(stoch_signal)

        # CCI Signals
        if 'cci' in df.columns:
            cci_signal = self.detect_cci_extreme(df, latest_index, latest_date, latest_price)
            if cci_signal:
                signals.append(cci_signal)

        # Williams %R Signals
        if 'williams_r' in df.columns:
            williams_signal = self.detect_williams_extreme(df, latest_index, latest_date, latest_price)
            if williams_signal:
                signals.append(williams_signal)

        # Bullish/Bearish Divergence
        if 'rsi' in df.columns and len(df) >= 20:
            divergence = self.detect_rsi_divergence(df, latest_index, latest_date, latest_price)
            if divergence:
                signals.append(divergence)

        return signals

    def detect_rsi_signals(self, df: pd.DataFrame, index: int, date: str, price: float) -> List[Signal]:
        """Detect RSI-based signals"""
        signals = []
        rsi = df['rsi'].iloc[index]

        if pd.isna(rsi):
            return signals

        # RSI Oversold (<30)
        if rsi < self.rsi_oversold:
            # Check if bouncing back
            if index > 0:
                prev_rsi = df['rsi'].iloc[index-1]
                bouncing = rsi > prev_rsi

                base_strength = 55.0 if bouncing else 45.0
                volume_conf = self.get_volume_confirmation(df, index)

                strength = self.calculate_strength(
                    base_strength,
                    volume_confirmed=volume_conf,
                    multiple_indicators=1 if bouncing else 0
                )

                signals.append(Signal(
                    signal_name="RSI Oversold",
                    signal_type=SignalType.MOMENTUM,
                    direction=SignalDirection.BULLISH,
                    strength=strength,
                    date=date,
                    price=price,
                    metadata={
                        'rsi': float(rsi),
                        'bouncing': bouncing,
                        'threshold': self.rsi_oversold
                    }
                ))

        # RSI Overbought (>70)
        elif rsi > self.rsi_overbought:
            if index > 0:
                prev_rsi = df['rsi'].iloc[index-1]
                rolling_over = rsi < prev_rsi

                base_strength = 55.0 if rolling_over else 45.0
                volume_conf = self.get_volume_confirmation(df, index)

                strength = self.calculate_strength(
                    base_strength,
                    volume_confirmed=volume_conf,
                    multiple_indicators=1 if rolling_over else 0
                )

                signals.append(Signal(
                    signal_name="RSI Overbought",
                    signal_type=SignalType.MOMENTUM,
                    direction=SignalDirection.BEARISH,
                    strength=strength,
                    date=date,
                    price=price,
                    metadata={
                        'rsi': float(rsi),
                        'rolling_over': rolling_over,
                        'threshold': self.rsi_overbought
                    }
                ))

        # RSI Midline Cross (50)
        if index > 0:
            prev_rsi = df['rsi'].iloc[index-1]

            # Bullish midline cross
            if prev_rsi < 50 and rsi > 50:
                strength = self.calculate_strength(
                    50.0,
                    trend_aligned=self.get_trend_alignment(df, index, bullish=True)
                )

                signals.append(Signal(
                    signal_name="RSI Bullish Midline Cross",
                    signal_type=SignalType.MOMENTUM,
                    direction=SignalDirection.BULLISH,
                    strength=strength,
                    date=date,
                    price=price,
                    metadata={'rsi': float(rsi)}
                ))

            # Bearish midline cross
            elif prev_rsi > 50 and rsi < 50:
                strength = self.calculate_strength(
                    50.0,
                    trend_aligned=self.get_trend_alignment(df, index, bullish=False)
                )

                signals.append(Signal(
                    signal_name="RSI Bearish Midline Cross",
                    signal_type=SignalType.MOMENTUM,
                    direction=SignalDirection.BEARISH,
                    strength=strength,
                    date=date,
                    price=price,
                    metadata={'rsi': float(rsi)}
                ))

        return signals

    def detect_stochastic_crossover(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect Stochastic %K crossing %D"""
        k = df['stoch_k'].iloc[index]
        d = df['stoch_d'].iloc[index]

        if pd.isna(k) or pd.isna(d):
            return None

        # Bullish crossover in oversold zone
        if self.is_crossover(df['stoch_k'], df['stoch_d'], index) and k < 20:
            base_strength = 60.0
            volume_conf = self.get_volume_confirmation(df, index)

            strength = self.calculate_strength(
                base_strength,
                volume_confirmed=volume_conf
            )

            return Signal(
                signal_name="Stochastic Bullish Crossover",
                signal_type=SignalType.MOMENTUM,
                direction=SignalDirection.BULLISH,
                strength=strength,
                date=date,
                price=price,
                metadata={
                    'stoch_k': float(k),
                    'stoch_d': float(d),
                    'in_oversold': True
                }
            )

        # Bearish crossover in overbought zone
        if self.is_crossunder(df['stoch_k'], df['stoch_d'], index) and k > 80:
            base_strength = 60.0
            volume_conf = self.get_volume_confirmation(df, index)

            strength = self.calculate_strength(
                base_strength,
                volume_confirmed=volume_conf
            )

            return Signal(
                signal_name="Stochastic Bearish Crossover",
                signal_type=SignalType.MOMENTUM,
                direction=SignalDirection.BEARISH,
                strength=strength,
                date=date,
                price=price,
                metadata={
                    'stoch_k': float(k),
                    'stoch_d': float(d),
                    'in_overbought': True
                }
            )

        return None

    def detect_cci_extreme(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect CCI extreme readings"""
        cci = df['cci'].iloc[index]

        if pd.isna(cci):
            return None

        # CCI > +100 (overbought)
        if cci > 100:
            return Signal(
                signal_name="CCI Overbought",
                signal_type=SignalType.MOMENTUM,
                direction=SignalDirection.BEARISH,
                strength=50.0,
                date=date,
                price=price,
                metadata={'cci': float(cci)}
            )

        # CCI < -100 (oversold)
        if cci < -100:
            return Signal(
                signal_name="CCI Oversold",
                signal_type=SignalType.MOMENTUM,
                direction=SignalDirection.BULLISH,
                strength=50.0,
                date=date,
                price=price,
                metadata={'cci': float(cci)}
            )

        return None

    def detect_williams_extreme(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect Williams %R extreme readings"""
        williams = df['williams_r'].iloc[index]

        if pd.isna(williams):
            return None

        # Williams %R > -20 (overbought)
        if williams > -20:
            return Signal(
                signal_name="Williams %R Overbought",
                signal_type=SignalType.MOMENTUM,
                direction=SignalDirection.BEARISH,
                strength=45.0,
                date=date,
                price=price,
                metadata={'williams_r': float(williams)}
            )

        # Williams %R < -80 (oversold)
        if williams < -80:
            return Signal(
                signal_name="Williams %R Oversold",
                signal_type=SignalType.MOMENTUM,
                direction=SignalDirection.BULLISH,
                strength=45.0,
                date=date,
                price=price,
                metadata={'williams_r': float(williams)}
            )

        return None

    def detect_rsi_divergence(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect bullish/bearish divergence between price and RSI"""
        if index < 10:
            return None

        # Look back 10-20 periods for divergence
        lookback = min(20, index)
        recent_data = df.iloc[index-lookback:index+1]

        close_prices = recent_data['close']
        rsi_values = recent_data['rsi']

        # Find peaks and troughs
        # Bullish Divergence: Price making lower lows, RSI making higher lows
        price_min_idx = close_prices.idxmin()
        rsi_at_price_min = rsi_values.loc[price_min_idx]

        # Check if there's a previous low
        before_min = close_prices.loc[:price_min_idx].iloc[:-1]
        if len(before_min) > 0:
            prev_price_min_idx = before_min.idxmin()
            prev_rsi_at_price_min = rsi_values.loc[prev_price_min_idx]

            # Bullish divergence
            if (close_prices.loc[price_min_idx] < close_prices.loc[prev_price_min_idx] and
                rsi_at_price_min > prev_rsi_at_price_min):

                return Signal(
                    signal_name="Bullish Divergence",
                    signal_type=SignalType.MOMENTUM,
                    direction=SignalDirection.BULLISH,
                    strength=65.0,
                    date=date,
                    price=price,
                    metadata={
                        'current_rsi': float(rsi_values.iloc[-1]),
                        'divergence_type': 'bullish'
                    }
                )

        # Bearish Divergence: Price making higher highs, RSI making lower highs
        price_max_idx = close_prices.idxmax()
        rsi_at_price_max = rsi_values.loc[price_max_idx]

        before_max = close_prices.loc[:price_max_idx].iloc[:-1]
        if len(before_max) > 0:
            prev_price_max_idx = before_max.idxmax()
            prev_rsi_at_price_max = rsi_values.loc[prev_price_max_idx]

            # Bearish divergence
            if (close_prices.loc[price_max_idx] > close_prices.loc[prev_price_max_idx] and
                rsi_at_price_max < prev_rsi_at_price_max):

                return Signal(
                    signal_name="Bearish Divergence",
                    signal_type=SignalType.MOMENTUM,
                    direction=SignalDirection.BEARISH,
                    strength=65.0,
                    date=date,
                    price=price,
                    metadata={
                        'current_rsi': float(rsi_values.iloc[-1]),
                        'divergence_type': 'bearish'
                    }
                )

        return None
