from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from apps.api.deps import get_db
from packages.services.dashboard import get_dashboard_summary
from packages.services.ticker_analysis import (
    bars_frame,
    get_current_feature_snapshot,
    get_recent_events,
    get_similar_historical_cases,
    get_ticker_or_404,
)

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    summary = get_dashboard_summary(db)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"summary": summary},
    )


@router.get("/api/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    return get_dashboard_summary(db)


@router.get("/ticker/{symbol}", response_class=HTMLResponse)
def ticker_detail_page(symbol: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    ticker = get_ticker_or_404(db, symbol)
    if ticker is None:
        raise HTTPException(status_code=404, detail="Ticker not found.")

    bars = bars_frame(db, ticker.id)
    events = get_recent_events(db, ticker.id)
    current_features = get_current_feature_snapshot(db, ticker.id)
    similar_cases = get_similar_historical_cases(db, ticker.id, current_features)

    bars_payload = []
    if not bars.empty:
        bars_payload = [
            {
                "date": row.date.isoformat(),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
            }
            for row in bars.tail(120).itertuples(index=False)
        ]

    return templates.TemplateResponse(
        request=request,
        name="ticker_detail.html",
        context={
            "ticker": ticker,
            "bars": bars_payload,
            "event_count": len(events),
            "events": events,
            "current_features": current_features or {},
            "similar_cases": similar_cases,
        },
    )
