from datetime import UTC, datetime, timedelta

import httpx
import pandas as pd

from packages.config import get_settings
from packages.core.data_providers.base import DailyBarProvider


class PolygonProvider(DailyBarProvider):
    base_url = "https://api.polygon.io"

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.polygon_api_key
        self.history_years = settings.bar_history_years
        self.timeout = 30.0

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def fetch_active_tickers(self, limit: int = 800) -> list[dict[str, str]]:
        if not self.api_key:
            return []

        collected: list[dict[str, str]] = []
        next_url = (
            f"{self.base_url}/v3/reference/tickers"
            "?market=stocks&active=true&limit=1000&sort=ticker&order=asc"
        )

        with httpx.Client(timeout=self.timeout) as client:
            while next_url and len(collected) < limit:
                response = client.get(next_url, params={"apiKey": self.api_key})
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("results", []):
                    ticker = item.get("ticker")
                    if not ticker:
                        continue
                    collected.append(
                        {
                            "symbol": ticker.upper(),
                            "exchange": item.get("primary_exchange") or item.get("market") or "US",
                        }
                    )
                    if len(collected) >= limit:
                        break
                next_url = payload.get("next_url")

        return collected[:limit]

    def fetch_daily_bars(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        if not self.api_key:
            return pd.DataFrame()

        end_date = datetime.now(UTC).date()
        start_date = end_date - timedelta(days=365 * self.history_years)
        url = (
            f"{self.base_url}/v2/aggs/ticker/{symbol.upper()}/range/1/day/"
            f"{start_date.isoformat()}/{end_date.isoformat()}"
        )
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
            "apiKey": self.api_key,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        results = payload.get("results", [])
        if not results:
            return pd.DataFrame()

        frame = pd.DataFrame(results)
        frame["date"] = pd.to_datetime(frame["t"], unit="ms", utc=True).dt.date
        frame = frame.rename(
            columns={
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume",
            }
        )
        return frame[["date", "open", "high", "low", "close", "volume"]].dropna()
