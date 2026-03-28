from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.deps import get_db
from packages.db.models.ticker import Ticker
from packages.schemas.ticker import TickerRead

router = APIRouter(tags=["tickers"])


@router.get("/tickers", response_model=list[TickerRead])
def list_tickers(db: Session = Depends(get_db)) -> list[TickerRead]:
    rows = db.scalars(select(Ticker).order_by(Ticker.symbol.asc())).all()
    return [TickerRead.model_validate(row) for row in rows]

