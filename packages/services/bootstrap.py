from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.config import get_settings
from packages.db.models import Ticker


def bootstrap_universe(db: Session) -> None:
    settings = get_settings()
    existing = set(db.scalars(select(Ticker.symbol)).all())
    for symbol in settings.universe_symbols:
        if symbol in existing:
            continue
        db.add(Ticker(symbol=symbol, exchange="NASDAQ", is_active=True))
    db.commit()

