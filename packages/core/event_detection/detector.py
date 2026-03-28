from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class PumpEventCandidate:
    base_date: date
    trigger_date: date
    peak_date: date
    base_price: float
    peak_price: float
    return_pct: float
    duration_days: int
    event_quality_score: float


class PumpEventDetector:
    def __init__(
        self,
        pump_multiplier: float = 2.0,
        base_lookback_days: int = 60,
        lookahead_days: int = 20,
    ) -> None:
        self.pump_multiplier = pump_multiplier
        self.base_lookback_days = base_lookback_days
        self.lookahead_days = lookahead_days

    def detect(self, bars: pd.DataFrame) -> list[PumpEventCandidate]:
        if bars.empty or len(bars) < self.base_lookback_days + self.lookahead_days:
            return []

        bars = bars.sort_values("date").reset_index(drop=True)
        results: list[PumpEventCandidate] = []
        last_peak_idx = -1

        for idx in range(self.base_lookback_days, len(bars) - self.lookahead_days):
            if idx <= last_peak_idx:
                continue

            base_window = bars.iloc[idx - self.base_lookback_days : idx]
            future_window = bars.iloc[idx : idx + self.lookahead_days]
            base_idx = base_window["low"].idxmin()
            base_row = bars.loc[base_idx]
            peak_idx = future_window["high"].idxmax()
            peak_row = bars.loc[peak_idx]

            if base_row["low"] <= 0 or peak_idx <= base_idx:
                continue

            multiple = peak_row["high"] / base_row["low"]
            if multiple < self.pump_multiplier:
                continue

            duration_days = int(peak_idx - base_idx)
            quality = min(100.0, (multiple - 1.0) * 40.0 + max(0, 20 - duration_days))
            results.append(
                PumpEventCandidate(
                    base_date=base_row["date"],
                    trigger_date=bars.loc[idx]["date"],
                    peak_date=peak_row["date"],
                    base_price=float(base_row["low"]),
                    peak_price=float(peak_row["high"]),
                    return_pct=float((multiple - 1.0) * 100.0),
                    duration_days=duration_days,
                    event_quality_score=quality,
                )
            )
            last_peak_idx = peak_idx

        return results

