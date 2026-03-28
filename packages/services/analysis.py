from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from packages.core.event_detection.detector import PumpEventDetector
from packages.core.feature_engine.extractor import FeatureExtractor
from packages.core.similarity.scorer import FEATURE_KEYS, euclidean_similarity, rule_based_score
from packages.db.models import DailyBar, FeatureSnapshot, PumpEvent, ScanResult, ScanRun, Ticker
from packages.services.data_ingestion import refresh_daily_bars


def create_scan_run(db: Session) -> ScanRun:
    run = ScanRun(status="running", tickers_scanned=0, candidates_found=0)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_latest_scan_run(db: Session) -> ScanRun | None:
    return db.scalars(select(ScanRun).order_by(ScanRun.started_at.desc())).first()


def get_running_scan_run(db: Session) -> ScanRun | None:
    return db.scalars(
        select(ScanRun).where(ScanRun.status == "running").order_by(ScanRun.started_at.desc())
    ).first()


def run_full_scan(db: Session, run: ScanRun | None = None) -> ScanRun:
    run = run or create_scan_run(db)

    tickers = db.scalars(select(Ticker).where(Ticker.is_active.is_(True))).all()
    refresh_daily_bars(db, tickers)
    try:
        _rebuild_pump_events(db, tickers)
        _rebuild_positive_snapshots(db, tickers)
        candidates_found = _build_live_scan_results(db, run.id, tickers)

        run.tickers_scanned = len(tickers)
        run.candidates_found = candidates_found
        run.status = "completed"
    except Exception:
        run.status = "failed"
        raise
    finally:
        run.finished_at = datetime.now(UTC)
        db.add(run)
        db.commit()
        db.refresh(run)
    return run


def _bars_frame(db: Session, ticker_id: int):
    import pandas as pd

    rows = db.execute(
        select(
            DailyBar.date,
            DailyBar.open,
            DailyBar.high,
            DailyBar.low,
            DailyBar.close,
            DailyBar.volume,
        )
        .where(DailyBar.ticker_id == ticker_id)
        .order_by(DailyBar.date.asc())
    ).all()
    return pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])


def _rebuild_pump_events(db: Session, tickers: list[Ticker]) -> None:
    detector = PumpEventDetector()
    for ticker in tickers:
        db.execute(delete(PumpEvent).where(PumpEvent.ticker_id == ticker.id))
        bars = _bars_frame(db, ticker.id)
        for candidate in detector.detect(bars):
            db.add(
                PumpEvent(
                    ticker_id=ticker.id,
                    base_date=candidate.base_date,
                    trigger_date=candidate.trigger_date,
                    peak_date=candidate.peak_date,
                    base_price=candidate.base_price,
                    peak_price=candidate.peak_price,
                    return_pct=candidate.return_pct,
                    duration_days=candidate.duration_days,
                    event_quality_score=candidate.event_quality_score,
                )
            )
    db.commit()


def _rebuild_positive_snapshots(db: Session, tickers: list[Ticker]) -> None:
    extractor = FeatureExtractor()
    for ticker in tickers:
        db.execute(delete(FeatureSnapshot).where(FeatureSnapshot.ticker_id == ticker.id))
        bars = _bars_frame(db, ticker.id)
        events = db.scalars(select(PumpEvent).where(PumpEvent.ticker_id == ticker.id)).all()
        for event in events:
            features = extractor.extract(bars, event.trigger_date)
            if features is None:
                continue
            db.add(
                FeatureSnapshot(
                    ticker_id=ticker.id,
                    event_id=event.id,
                    reference_date=event.trigger_date,
                    is_positive_case=True,
                    **features,
                )
            )
    db.commit()


def _build_live_scan_results(db: Session, run_id: int, tickers: list[Ticker]) -> int:
    extractor = FeatureExtractor()
    historical = db.scalars(
        select(FeatureSnapshot).where(FeatureSnapshot.is_positive_case.is_(True))
    ).all()
    historical_features = [
        {key: getattr(snapshot, key) for key in FEATURE_KEYS + ["avg_dollar_volume_20d"]}
        for snapshot in historical
    ]

    results = 0
    for ticker in tickers:
        bars = _bars_frame(db, ticker.id)
        if bars.empty:
            continue
        features = extractor.extract(bars, bars.iloc[-1]["date"])
        if features is None:
            continue

        similarities = [
            euclidean_similarity(features, historical_row) for historical_row in historical_features
        ]
        top_matches = sorted(similarities, reverse=True)[:10]
        avg_similarity = sum(top_matches) / len(top_matches) if top_matches else 0.0
        score = rule_based_score(features) + (avg_similarity * 10.0)

        db.add(
            ScanResult(
                run_id=run_id,
                ticker_id=ticker.id,
                score=score,
                similarity_score=avg_similarity,
                matched_pattern_count=len([value for value in top_matches if value > 0.15]),
                explanation_json={
                    "symbol": ticker.symbol,
                    "top_similarity": round(avg_similarity, 4),
                    "rv_ratio": round(features["rv_ratio"], 4),
                    "breakout_distance": round(features["breakout_distance"], 4),
                    "ret_20d": round(features["ret_20d"], 4),
                },
            )
        )
        results += 1

    db.commit()
    return results
