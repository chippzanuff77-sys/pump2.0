from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.deps import get_db
from packages.db.models.daily_bar import DailyBar
from packages.db.models.pump_event import PumpEvent
from packages.db.models.ticker import Ticker
from packages.schemas.event import PumpEventRead
from packages.schemas.ticker import TickerDetail, TickerRead

router = APIRouter(tags=["tickers"])


@router.get("/tickers", response_model=list[TickerRead])
def list_tickers(db: Session = Depends(get_db)) -> list[TickerRead]:
    rows = db.scalars(select(Ticker).order_by(Ticker.symbol.asc())).all()
    return [TickerRead.model_validate(row) for row in rows]


@router.get("/tickers/{symbol}", response_model=TickerDetail)
def get_ticker(symbol: str, db: Session = Depends(get_db)) -> TickerDetail:
    ticker = db.scalars(select(Ticker).where(Ticker.symbol == symbol.upper())).first()
    if ticker is None:
        raise HTTPException(status_code=404, detail="Ticker not found.")

    bar_count = (
        db.scalar(select(func.count()).select_from(DailyBar).where(DailyBar.ticker_id == ticker.id))
        or 0
    )
    event_count = (
        db.scalar(select(func.count()).select_from(PumpEvent).where(PumpEvent.ticker_id == ticker.id))
        or 0
    )
    return TickerDetail(
        id=ticker.id,
        symbol=ticker.symbol,
        exchange=ticker.exchange,
        is_active=ticker.is_active,
        sector=ticker.sector,
        industry=ticker.industry,
        bar_count=bar_count,
        event_count=event_count,
    )


@router.get("/events/{symbol}", response_model=list[PumpEventRead])
def get_ticker_events(symbol: str, db: Session = Depends(get_db)) -> list[PumpEventRead]:
    ticker = db.scalars(select(Ticker).where(Ticker.symbol == symbol.upper())).first()
    if ticker is None:
        raise HTTPException(status_code=404, detail="Ticker not found.")

    events = db.scalars(
        select(PumpEvent)
        .where(PumpEvent.ticker_id == ticker.id)
        .order_by(PumpEvent.trigger_date.desc())
    ).all()
    return [PumpEventRead.model_validate(event) for event in events]
