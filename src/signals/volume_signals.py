"""
Volume-based signal detectors
Volume breakouts, OBV divergence, Chaikin Money Flow, etc.
"""

import pandas as pd
from typing import List, Dict

from .detector import BaseSignalDetector, Signal, SignalType, SignalDirection


class VolumeSignalDetector(BaseSignalDetector):
    """Detect volume-based trading signals"""

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.volume_breakout_threshold = config.get('volume_breakout_threshold', 2.0) if config else 2.0

    def detect(self, df: pd.DataFrame) -> List[Signal]:
        """Detect all volume signals"""
        signals = []

        if len(df) < 2:
            return signals

        latest_index = len(df) - 1
        latest_date = df.index[latest_index].strftime('%Y-%m-%d')
        latest_price = df['close'].iloc[latest_index]

        # Volume breakout
        if 'volume_sma' in df.columns:
            vol_signal = self.detect_volume_breakout(df, latest_index, latest_date, latest_price)
            if vol_signal:
                signals.append(vol_signal)

        # OBV divergence
        if 'obv' in df.columns and len(df) >= 20:
            obv_signal = self.detect_obv_divergence(df, latest_index, latest_date, latest_price)
            if obv_signal:
                signals.append(obv_signal)

        # Chaikin Money Flow
        if 'cmf' in df.columns:
            cmf_signal = self.detect_cmf_signal(df, latest_index, latest_date, latest_price)
            if cmf_signal:
                signals.append(cmf_signal)

        # Money Flow Index
        if 'mfi' in df.columns:
            mfi_signal = self.detect_mfi_extreme(df, latest_index, latest_date, latest_price)
            if mfi_signal:
                signals.append(mfi_signal)

        return signals

    def detect_volume_breakout(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect volume breakout (volume spike)"""
        current_volume = df['volume'].iloc[index]
        avg_volume = df['volume_sma'].iloc[index]

        if pd.isna(avg_volume) or avg_volume == 0:
            return None

        volume_ratio = current_volume / avg_volume

        # Volume breakout (> 2x average by default)
        if volume_ratio > self.volume_breakout_threshold:
            # Determine direction based on price movement
            if index > 0:
                prev_close = df['close'].iloc[index-1]
                current_close = df['close'].iloc[index]

                if current_close > prev_close:
                    direction = SignalDirection.BULLISH
                    signal_name = "Volume Breakout Bullish"
                    base_strength = 65.0
                else:
                    direction = SignalDirection.BEARISH
                    signal_name = "Volume Breakout Bearish"
                    base_strength = 65.0

                # Higher volume ratio = stronger signal
                strength_bonus = min((volume_ratio - self.volume_breakout_threshold) * 5, 20)
                strength = min(base_strength + strength_bonus, 100.0)

                return Signal(
                    signal_name=signal_name,
                    signal_type=SignalType.VOLUME,
                    direction=direction,
                    strength=strength,
                    date=date,
                    price=price,
                    metadata={
                        'volume': int(current_volume),
                        'avg_volume': int(avg_volume),
                        'volume_ratio': float(volume_ratio)
                    }
                )

        return None

    def detect_obv_divergence(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect OBV divergence from price"""
        if index < 10:
            return None

        lookback = min(20, index)
        recent_data = df.iloc[index-lookback:index+1]

        close_prices = recent_data['close']
        obv_values = recent_data['obv']

        # Bullish divergence: Price lower low, OBV higher low
        price_min_idx = close_prices.idxmin()
        obv_at_price_min = obv_values.loc[price_min_idx]

        before_min = close_prices.loc[:price_min_idx].iloc[:-1]
        if len(before_min) > 0:
            prev_price_min_idx = before_min.idxmin()
            prev_obv_at_price_min = obv_values.loc[prev_price_min_idx]

            if (close_prices.loc[price_min_idx] < close_prices.loc[prev_price_min_idx] and
                obv_at_price_min > prev_obv_at_price_min):

                return Signal(
                    signal_name="OBV Bullish Divergence",
                    signal_type=SignalType.VOLUME,
                    direction=SignalDirection.BULLISH,
                    strength=60.0,
                    date=date,
                    price=price,
                    metadata={'divergence_type': 'bullish'}
                )

        # Bearish divergence: Price higher high, OBV lower high
        price_max_idx = close_prices.idxmax()
        obv_at_price_max = obv_values.loc[price_max_idx]

        before_max = close_prices.loc[:price_max_idx].iloc[:-1]
        if len(before_max) > 0:
            prev_price_max_idx = before_max.idxmax()
            prev_obv_at_price_max = obv_values.loc[prev_price_max_idx]

            if (close_prices.loc[price_max_idx] > close_prices.loc[prev_price_max_idx] and
                obv_at_price_max < prev_obv_at_price_max):

                return Signal(
                    signal_name="OBV Bearish Divergence",
                    signal_type=SignalType.VOLUME,
                    direction=SignalDirection.BEARISH,
                    strength=60.0,
                    date=date,
                    price=price,
                    metadata={'divergence_type': 'bearish'}
                )

        return None

    def detect_cmf_signal(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect Chaikin Money Flow extreme values"""
        cmf = df['cmf'].iloc[index]

        if pd.isna(cmf):
            return None

        # Strong buying pressure
        if cmf > 0.2:
            return Signal(
                signal_name="Strong Buying Pressure",
                signal_type=SignalType.VOLUME,
                direction=SignalDirection.BULLISH,
                strength=55.0,
                date=date,
                price=price,
                metadata={'cmf': float(cmf)}
            )

        # Strong selling pressure
        if cmf < -0.2:
            return Signal(
                signal_name="Strong Selling Pressure",
                signal_type=SignalType.VOLUME,
                direction=SignalDirection.BEARISH,
                strength=55.0,
                date=date,
                price=price,
                metadata={'cmf': float(cmf)}
            )

        return None

    def detect_mfi_extreme(self, df: pd.DataFrame, index: int, date: str, price: float) -> Signal:
        """Detect Money Flow Index extremes"""
        mfi = df['mfi'].iloc[index]

        if pd.isna(mfi):
            return None

        # MFI Oversold (<20)
        if mfi < 20:
            return Signal(
                signal_name="MFI Oversold",
                signal_type=SignalType.VOLUME,
                direction=SignalDirection.BULLISH,
                strength=50.0,
                date=date,
                price=price,
                metadata={'mfi': float(mfi)}
            )

        # MFI Overbought (>80)
        if mfi > 80:
            return Signal(
                signal_name="MFI Overbought",
                signal_type=SignalType.VOLUME,
                direction=SignalDirection.BEARISH,
                strength=50.0,
                date=date,
                price=price,
                metadata={'mfi': float(mfi)}
            )

        return None
