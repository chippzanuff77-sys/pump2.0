from datetime import date

import numpy as np
import pandas as pd


def _safe_pct_change(current: float, past: float) -> float:
    if past == 0 or np.isnan(current) or np.isnan(past):
        return 0.0
    return ((current / past) - 1.0) * 100.0


class FeatureExtractor:
    def extract(self, bars: pd.DataFrame, reference_date: date) -> dict[str, float] | None:
        if bars.empty:
            return None

        bars = bars.sort_values("date").reset_index(drop=True)
        ref_rows = bars.index[bars["date"] == reference_date].tolist()
        if not ref_rows:
            return None

        ref_idx = ref_rows[0]
        if ref_idx < 30:
            return None

        window = bars.iloc[: ref_idx + 1].copy()
        current_close = float(window.iloc[-1]["close"])
        current_volume = float(window.iloc[-1]["volume"])

        close_5 = float(window.iloc[-6]["close"])
        close_10 = float(window.iloc[-11]["close"])
        close_20 = float(window.iloc[-21]["close"])
        close_30 = float(window.iloc[-31]["close"])

        sma20 = float(window["close"].tail(20).mean())
        sma50 = float(window["close"].tail(min(50, len(window))).mean())
        avg_volume_20 = float(window["volume"].tail(20).mean())
        high_20 = float(window["high"].tail(20).max())
        low_10 = float(window["low"].tail(10).min())
        high_10 = float(window["high"].tail(10).max())

        daily_ranges = (window["high"].tail(14) - window["low"].tail(14)).astype(float)
        atr_pct = float((daily_ranges.mean() / current_close) * 100.0) if current_close else 0.0

        returns = window["close"].pct_change().dropna().tail(10)
        volatility_10 = float(returns.std() * np.sqrt(252) * 100.0) if not returns.empty else 0.0

        gain = window["close"].diff().clip(lower=0).tail(14).mean()
        loss = (-window["close"].diff().clip(upper=0)).tail(14).mean()
        rs = float(gain / loss) if loss and not np.isnan(loss) else 0.0
        rsi_14 = 100.0 - (100.0 / (1.0 + rs)) if rs else 100.0

        range_compression_score = float(
            1.0 - ((high_10 - low_10) / current_close)
        ) if current_close else 0.0
        breakout_distance = float(((current_close / high_20) - 1.0) * 100.0) if high_20 else 0.0

        return {
            "ret_5d": _safe_pct_change(current_close, close_5),
            "ret_10d": _safe_pct_change(current_close, close_10),
            "ret_20d": _safe_pct_change(current_close, close_20),
            "ret_30d": _safe_pct_change(current_close, close_30),
            "rv_ratio": (current_volume / avg_volume_20) if avg_volume_20 else 0.0,
            "atr_pct": atr_pct,
            "volatility_10d": volatility_10,
            "range_compression_score": range_compression_score,
            "breakout_distance": breakout_distance,
            "rsi_14": float(rsi_14),
            "sma20_distance": float(((current_close / sma20) - 1.0) * 100.0) if sma20 else 0.0,
            "sma50_distance": float(((current_close / sma50) - 1.0) * 100.0) if sma50 else 0.0,
            "avg_dollar_volume_20d": avg_volume_20 * current_close,
        }

