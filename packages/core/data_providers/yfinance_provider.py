import pandas as pd
import yfinance as yf

from packages.core.data_providers.base import DailyBarProvider


class YFinanceDailyBarProvider(DailyBarProvider):
    def fetch_daily_bars(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        frame = yf.Ticker(symbol).history(period=period, auto_adjust=False, actions=True)
        if frame.empty:
            return pd.DataFrame()

        frame = frame.reset_index()
        frame = frame.rename(
            columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        frame["date"] = pd.to_datetime(frame["date"]).dt.date
        for column in ["open", "high", "low", "close", "volume"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        return frame[["date", "open", "high", "low", "close", "volume"]].dropna()

