"""
Volatility-based signal detectors
Bollinger Band breakouts, squeezes, ATR signals, etc.
"""

import pandas as pd
from typing import List

from .detector import BaseSignalDetector, Signal, SignalType, SignalDirection


class VolatilitySignalDetector(BaseSignalDetector):
    """Detect volatility-based trading signals"""

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """Detect all volatility signals"""
        signals = []

        if len(df) < 2:
            return signals

        latest_index = len(df) - 1
        latest_date = df.index[latest_index].strftime('%Y-%m-%d')
        latest_price = df['close'].iloc[latest_index]

        # Bollinger Band signals
        if all(col in df.columns for col in ['bb_upper', 'bb_lower', 'bb_width', 'percent_b']):
            bb_signals = self.detect_bollinger_signals(df, latest_index, latest_date, latest_price)
            signals.extend(bb_signals)

        # ATR signals
        if 'atr' in df.columns and len(df) >= 20:
            atr_signal = self.detect_atr_expansion(df, latest_index, latest_date, latest_price)
            if atr_signal:
                signals.append(atr_signal)

        return signals

    def detect_bollinger_signals(self, df: pd.DataFrame, index: int, date: str, price: float) -> List[Signal]:
        """Detect Bollinger Band signals"""
        signals = []

        close = df['close'].iloc[index]
        bb_upper = df['bb_upper'].iloc[index]
        bb_lower = df['bb_lower'].iloc[index]
        bb_width = df['bb_width'].iloc[index]
        percent_b = df['percent_b'].iloc[index]

        # Bollinger Band Squeeze (low volatility, potential breakout)
        if index >= 20:
            avg_width = df['bb_width'].iloc[index-20:index].mean()
            if bb_width < avg_width * 0.5:  # Current width < 50% of recent average
                signals.append(Signal(
                    signal_name="Bollinger Band Squeeze",
                    signal_type=SignalType.VOLATILITY,
                    direction=SignalDirection.NEUTRAL,
                    strength=55.0,
                    date=date,
                    price=price,
                    metadata={'bb_width': float(bb_width), 'avg_width': float(avg_width)}
                ))

        # Bollinger Band Breakout
        if index > 0:
            prev_close = df['close'].iloc[index-1]
            prev_bb_upper = df['bb_upper'].iloc[index-1]
            prev_bb_lower = df['bb_lower'].iloc[index-1]

            # Bullish breakout (close breaks above upper band)
            if prev_close < prev_bb_upper and close > bb_upper:
                volume_conf = self.get_volume_confirmation(df, index)
                strength = self.calculate_strength(60.0, volume_confirmed=volume_conf)

                signals.append(Signal(
                    signal_name="Bollinger Band Bullish Breakout",
                    signal_type=SignalType.VOLATILITY,
                    direction=SignalDirection.BULLISH,
                    strength=strength,
                    date=date,
                    price=price,
                    metadata={'percent_b': float(percent_b)}
                ))

            # Bearish breakout (close breaks below lower band)
            elif prev_close > prev_bb_lower and close < bb_lower:
                volume_conf = self.get_volume_confirmation(df, index)
                strength = self.calculate_strength(60.0, volume_confirmed=volume_conf)

                signals.append(Signal(
                    signal_name="Bollinger Band Bearish Breakout",
                    signal_type=SignalType.VOLATILITY,
                    direction=SignalDirection.BEARISH,
                    strength=strength,
                    date=date,
                    price=price,
                    metadata={'percent_b': float(percent_b)}
                ))

        # Walking the Bands (strong trend)
        if percent_b > 0.9:  # Close near upper band
            signals.append(Signal(
                signal_name="Walking Upper Band",
                signal_type=SignalType.VOLATILITY,
                direction=SignalDirection.BULLISH,
                strength=50.0,
                date=date,
                price=price,
                metadata={'percent_b': float(percent_b)}
            ))
        elif percent_b < 0.1:  # Close near lower band
            signals.append(Signal(
                signal_name="Walking Lower Band",
                signal_type=SignalType.VOLATILITY,
                direction=SignalDirection.BEARISH,
                strength=50.0,
                date=date,
                price=price,
                metadata={'percent_b': float(percent_b)}
            ))

        return signals

    def detect_atr_expansion(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect ATR expansion (increased volatility)"""
        current_atr = df['atr'].iloc[index]
        avg_atr = df['atr'].iloc[index-20:index].mean()

        # ATR expansion (current > 1.5x average)
        if current_atr > avg_atr * 1.5:
            return Signal(
                signal_name="ATR Expansion",
                signal_type=SignalType.VOLATILITY,
                direction=SignalDirection.NEUTRAL,
                strength=45.0,
                date=date,
                price=price,
                metadata={'atr': float(current_atr), 'avg_atr': float(avg_atr)}
            )

        return None
