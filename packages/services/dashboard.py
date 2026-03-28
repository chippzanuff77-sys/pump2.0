from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.db.models import PumpEvent, ScanResult, ScanRun, Ticker
from packages.schemas.dashboard import DashboardSummary


def get_dashboard_summary(db: Session) -> DashboardSummary:
    ticker_count = db.scalar(select(func.count()).select_from(Ticker)) or 0
    event_count = db.scalar(select(func.count()).select_from(PumpEvent)) or 0
    latest_run = db.scalars(select(ScanRun).order_by(ScanRun.started_at.desc())).first()

    top_score = 0.0
    if latest_run is not None:
        top_score = (
            db.scalar(
                select(func.max(ScanResult.score)).where(ScanResult.run_id == latest_run.id)
            )
            or 0.0
        )

    return DashboardSummary(
        ticker_count=ticker_count,
        event_count=event_count,
        latest_run_id=latest_run.id if latest_run else None,
        latest_run_status=latest_run.status if latest_run else None,
        latest_run_started_at=latest_run.started_at if latest_run else None,
        latest_run_finished_at=latest_run.finished_at if latest_run else None,
        latest_run_candidates=latest_run.candidates_found if latest_run else 0,
        top_score=float(top_score),
    )
