from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.config import get_settings
from packages.core.data_providers.polygon_provider import PolygonProvider
from packages.db.models import Ticker


def bootstrap_universe(db: Session) -> None:
    settings = get_settings()
    existing = set(db.scalars(select(Ticker.symbol)).all())

    provider = PolygonProvider()
    if settings.market_data_provider == "polygon" and provider.is_configured():
        remote_tickers = provider.fetch_active_tickers(limit=settings.universe_limit)
        remote_symbols = {item["symbol"] for item in remote_tickers}

        for item in remote_tickers:
            symbol = item["symbol"]
            ticker = db.scalars(select(Ticker).where(Ticker.symbol == symbol)).first()
            if ticker is None:
                db.add(Ticker(symbol=symbol, exchange=item["exchange"], is_active=True))
                continue
            ticker.exchange = item["exchange"]
            ticker.is_active = True

        if remote_symbols:
            inactive_rows = db.scalars(select(Ticker).where(Ticker.symbol.not_in(remote_symbols))).all()
            for ticker in inactive_rows:
                ticker.is_active = False
    else:
        for symbol in settings.universe_symbols:
            if symbol in existing:
                continue
            db.add(Ticker(symbol=symbol, exchange="NASDAQ", is_active=True))

    db.commit()
