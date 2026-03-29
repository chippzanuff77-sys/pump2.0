from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from packages.core.event_detection.detector import PumpEventDetector
from packages.core.feature_engine.extractor import FeatureExtractor
from packages.core.similarity.scorer import FEATURE_KEYS, euclidean_similarity, rule_based_score
from packages.config import get_settings
from packages.db.models import DailyBar, FeatureSnapshot, PatternSnapshot, PumpEvent, ScanResult, ScanRun, Ticker
from packages.services.bootstrap import bootstrap_universe
from packages.services.data_ingestion import refresh_daily_bars

HISTORICAL_WINDOWS = {
    "pre_30": 30,
    "pre_10": 10,
    "pre_5": 5,
    "pre_1": 1,
    "trigger_day": 0,
}


def create_scan_run(db: Session) -> ScanRun:
    run = ScanRun(status="running", tickers_scanned=0, candidates_found=0)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def reset_system_state(db: Session) -> None:
    db.execute(delete(ScanResult))
    db.execute(delete(ScanRun))
    db.execute(delete(PatternSnapshot))
    db.execute(delete(FeatureSnapshot))
    db.execute(delete(PumpEvent))
    db.execute(delete(DailyBar))
    db.execute(delete(Ticker))
    db.commit()


def get_latest_scan_run(db: Session) -> ScanRun | None:
    return db.scalars(select(ScanRun).order_by(ScanRun.started_at.desc())).first()


def get_running_scan_run(db: Session) -> ScanRun | None:
    return db.scalars(
        select(ScanRun).where(ScanRun.status == "running").order_by(ScanRun.started_at.desc())
    ).first()


def run_full_scan(
    db: Session,
    run: ScanRun | None = None,
    reset_before_run: bool = False,
) -> ScanRun:
    if reset_before_run:
        reset_system_state(db)

    run = run or create_scan_run(db)

    bootstrap_universe(db)
    tickers = db.scalars(select(Ticker).where(Ticker.is_active.is_(True))).all()
    refresh_daily_bars(db, tickers)
    try:
        _rebuild_pump_events(db, tickers)
        _rebuild_positive_snapshots(db, tickers)
        _rebuild_pattern_library(db, tickers)
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
    settings = get_settings()
    detector = PumpEventDetector(
        pump_multiplier=settings.pump_multiplier,
        base_lookback_days=settings.pump_base_lookback_days,
        lookahead_days=settings.pump_lookahead_days,
    )
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


def _rebuild_pattern_library(db: Session, tickers: list[Ticker]) -> None:
    extractor = FeatureExtractor()
    for ticker in tickers:
        db.execute(delete(PatternSnapshot).where(PatternSnapshot.ticker_id == ticker.id))
        bars = _bars_frame(db, ticker.id)
        if bars.empty:
            continue

        events = db.scalars(select(PumpEvent).where(PumpEvent.ticker_id == ticker.id)).all()
        for event in events:
            for window_type, offset in HISTORICAL_WINDOWS.items():
                reference_candidates = bars.index[bars["date"] == event.trigger_date].tolist()
                if not reference_candidates:
                    continue

                reference_idx = reference_candidates[0] - offset
                if reference_idx < 30 or reference_idx >= len(bars):
                    continue

                reference_date = bars.iloc[reference_idx]["date"]
                features = extractor.extract(bars, reference_date)
                if features is None:
                    continue

                db.add(
                    PatternSnapshot(
                        ticker_id=ticker.id,
                        event_id=event.id,
                        reference_date=reference_date,
                        snapshot_kind="historical",
                        window_type=window_type,
                        **features,
                    )
                )
    db.commit()


def _build_live_scan_results(db: Session, run_id: int, tickers: list[Ticker]) -> int:
    extractor = FeatureExtractor()
    historical = db.scalars(
        select(PatternSnapshot)
        .where(PatternSnapshot.snapshot_kind == "historical")
        .where(PatternSnapshot.window_type != "trigger_day")
    ).all()

    results = 0
    for ticker in tickers:
        db.execute(
            delete(PatternSnapshot)
            .where(PatternSnapshot.ticker_id == ticker.id)
            .where(PatternSnapshot.snapshot_kind == "live")
        )
        bars = _bars_frame(db, ticker.id)
        if bars.empty:
            continue
        features = extractor.extract(bars, bars.iloc[-1]["date"])
        if features is None:
            continue

        db.add(
            PatternSnapshot(
                ticker_id=ticker.id,
                event_id=None,
                reference_date=bars.iloc[-1]["date"],
                snapshot_kind="live",
                window_type="current",
                **features,
            )
        )

        scored_matches: list[tuple[float, PatternSnapshot]] = []
        for snapshot in historical:
            historical_row = {key: getattr(snapshot, key) for key in FEATURE_KEYS}
            scored_matches.append((euclidean_similarity(features, historical_row), snapshot))

        scored_matches.sort(key=lambda item: item[0], reverse=True)
        top_matches = scored_matches[:10]
        top_scores = [score for score, _snapshot in top_matches]
        window_counts: dict[str, int] = {}
        matched_symbols: list[str] = []
        matched_cases: list[dict] = []
        for _score, snapshot in top_matches:
            window_counts[snapshot.window_type] = window_counts.get(snapshot.window_type, 0) + 1
            if snapshot.ticker and snapshot.ticker.symbol not in matched_symbols:
                matched_symbols.append(snapshot.ticker.symbol)
            if snapshot.ticker and snapshot.event:
                matched_cases.append(
                    {
                        "symbol": snapshot.ticker.symbol,
                        "window_type": snapshot.window_type,
                        "similarity": round(_score, 4),
                        "trigger_date": snapshot.event.trigger_date.isoformat(),
                        "return_pct": round(snapshot.event.return_pct, 2),
                    }
                )

        avg_similarity = sum(top_scores) / len(top_scores) if top_scores else 0.0
        rule_score = rule_based_score(features)
        similarity_component = avg_similarity * 10.0
        score = rule_score + similarity_component

        db.add(
            ScanResult(
                run_id=run_id,
                ticker_id=ticker.id,
                score=score,
                similarity_score=avg_similarity,
                matched_pattern_count=len([value for value in top_scores if value > 0.15]),
                explanation_json={
                    "symbol": ticker.symbol,
                    "top_similarity": round(avg_similarity, 4),
                    "rv_ratio": round(features["rv_ratio"], 4),
                    "breakout_distance": round(features["breakout_distance"], 4),
                    "ret_20d": round(features["ret_20d"], 4),
                    "matched_symbols": matched_symbols[:5],
                    "window_counts": window_counts,
                    "matched_cases": matched_cases[:5],
                    "score_breakdown": {
                        "rule_score": round(rule_score, 4),
                        "similarity_component": round(similarity_component, 4),
                        "final_score": round(score, 4),
                    },
                },
            )
        )
        results += 1

    db.commit()
    return results
