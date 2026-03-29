from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.config import get_settings
from packages.core.data_providers.finviz_provider import FinvizUniverseProvider
from packages.core.data_providers.polygon_provider import PolygonProvider
from packages.db.models import Ticker


def bootstrap_universe(db: Session) -> None:
    settings = get_settings()
    existing = set(db.scalars(select(Ticker.symbol)).all())

    collected: list[dict[str, str]] = []
    seen_symbols: set[str] = set()

    def extend_candidates(items: list[dict[str, str]]) -> None:
        for item in items:
            symbol = item["symbol"].upper()
            if symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            collected.append({"symbol": symbol, "exchange": item.get("exchange") or "US"})
            if len(collected) >= settings.universe_limit:
                break

    if "polygon" in settings.enabled_universe_sources:
        provider = PolygonProvider()
        if provider.is_configured():
            extend_candidates(provider.fetch_active_tickers(limit=settings.universe_limit))

    if len(collected) < settings.universe_limit and "finviz" in settings.enabled_universe_sources:
        provider = FinvizUniverseProvider()
        extend_candidates(provider.fetch_symbols(limit=settings.universe_limit))

    if collected:
        remote_symbols = {item["symbol"] for item in collected}

        for item in collected:
            symbol = item["symbol"]
            ticker = db.scalars(select(Ticker).where(Ticker.symbol == symbol)).first()
            if ticker is None:
                db.add(Ticker(symbol=symbol, exchange=item["exchange"], is_active=True))
                continue
            ticker.exchange = item["exchange"]
            ticker.is_active = True

        inactive_rows = db.scalars(select(Ticker).where(Ticker.symbol.not_in(remote_symbols))).all()
        for ticker in inactive_rows:
            ticker.is_active = False
    else:
        for symbol in settings.universe_symbols:
            if symbol in existing:
                continue
            db.add(Ticker(symbol=symbol, exchange="NASDAQ", is_active=True))

    db.commit()
