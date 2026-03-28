from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.config import get_settings
from packages.core.data_providers.polygon_provider import PolygonProvider
from packages.core.data_providers.yfinance_provider import YFinanceDailyBarProvider
from packages.db.models import DailyBar, Ticker


def refresh_daily_bars(db: Session, tickers: list[Ticker] | None = None) -> None:
    settings = get_settings()
    polygon_provider = PolygonProvider()
    provider = (
        polygon_provider
        if settings.market_data_provider == "polygon" and polygon_provider.is_configured()
        else YFinanceDailyBarProvider()
    )
    tickers = tickers or db.scalars(select(Ticker).where(Ticker.is_active.is_(True))).all()

    for ticker in tickers:
        frame = provider.fetch_daily_bars(ticker.symbol)
        if frame.empty:
            continue

        db.query(DailyBar).filter(DailyBar.ticker_id == ticker.id).delete()
        for _, row in frame.iterrows():
            db.add(
                DailyBar(
                    ticker_id=ticker.id,
                    date=row["date"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )
    db.commit()
