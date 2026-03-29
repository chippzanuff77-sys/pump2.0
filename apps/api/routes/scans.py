from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.deps import get_db
from packages.db.session import SessionLocal
from packages.db.models.scan_result import ScanResult
from packages.db.models.scan_run import ScanRun
from packages.db.models.ticker import Ticker
from packages.schemas.scan import (
    ScanResultWithTicker,
    ScanRunRead,
    TriggerScanResponse,
)
from packages.services.analysis import (
    create_scan_run,
    get_latest_scan_run,
    get_running_scan_run,
    reset_system_state,
    run_full_scan,
)

router = APIRouter(tags=["scans"])


def _run_scan_in_background(run_id: int) -> None:
    with SessionLocal() as db:
        run = db.get(ScanRun, run_id)
        if run is None:
            return
        run_full_scan(db, run=run)


def _reset_and_run_scan_in_background() -> None:
    with SessionLocal() as db:
        run_full_scan(db, reset_before_run=True)


@router.post("/scan/run", response_model=TriggerScanResponse)
def trigger_scan(background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> TriggerScanResponse:
    running = get_running_scan_run(db)
    if running is not None:
        return TriggerScanResponse(
            run_id=running.id,
            status=running.status,
            message="A scan is already running.",
        )

    reset_system_state(db)
    run = create_scan_run(db)
    background_tasks.add_task(_run_scan_in_background, run.id)
    return TriggerScanResponse(
        run_id=run.id,
        status="running",
        message="System reset and x4 scan started in the background.",
    )


@router.get("/scan/latest", response_model=ScanRunRead)
def latest_scan(db: Session = Depends(get_db)) -> ScanRunRead:
    run = get_latest_scan_run(db)
    if run is None:
        raise HTTPException(status_code=404, detail="No scan runs found.")
    return ScanRunRead.model_validate(run)


@router.get("/scan/runs", response_model=list[ScanRunRead])
def list_scan_runs(limit: int = 10, db: Session = Depends(get_db)) -> list[ScanRunRead]:
    rows = db.scalars(select(ScanRun).order_by(ScanRun.started_at.desc()).limit(limit)).all()
    return [ScanRunRead.model_validate(row) for row in rows]


@router.get("/signals/top", response_model=list[ScanResultWithTicker])
def top_signals(limit: int = 20, db: Session = Depends(get_db)) -> list[ScanResultWithTicker]:
    latest_run = db.scalars(select(ScanRun).order_by(ScanRun.started_at.desc())).first()
    if latest_run is None:
        raise HTTPException(status_code=404, detail="No scan runs found.")

    rows = db.execute(
        select(ScanResult)
        .join(Ticker, Ticker.id == ScanResult.ticker_id)
        .where(ScanResult.run_id == latest_run.id)
        .order_by(ScanResult.score.desc(), ScanResult.similarity_score.desc())
        .limit(limit)
    ).scalars().all()
    return [
        ScanResultWithTicker(
            id=row.id,
            run_id=row.run_id,
            ticker_id=row.ticker_id,
            score=row.score,
            similarity_score=row.similarity_score,
            matched_pattern_count=row.matched_pattern_count,
            explanation_json=row.explanation_json,
            symbol=row.ticker.symbol,
        )
        for row in rows
    ]
