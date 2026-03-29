from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.db.models import PatternSnapshot, PumpEvent


def get_common_patterns_summary(db: Session) -> dict:
    event_count = db.scalar(select(func.count()).select_from(PumpEvent)) or 0
    historical_count = (
        db.scalar(
            select(func.count())
            .select_from(PatternSnapshot)
            .where(PatternSnapshot.snapshot_kind == "historical")
        )
        or 0
    )

    window_rows = db.execute(
        select(
            PatternSnapshot.window_type,
            func.count().label("count"),
            func.avg(PatternSnapshot.rv_ratio).label("avg_rv_ratio"),
            func.avg(PatternSnapshot.breakout_distance).label("avg_breakout_distance"),
            func.avg(PatternSnapshot.ret_20d).label("avg_ret_20d"),
            func.avg(PatternSnapshot.atr_pct).label("avg_atr_pct"),
        )
        .where(PatternSnapshot.snapshot_kind == "historical")
        .group_by(PatternSnapshot.window_type)
        .order_by(PatternSnapshot.window_type.asc())
    ).all()

    top_quality_events = db.scalars(
        select(PumpEvent).order_by(PumpEvent.event_quality_score.desc()).limit(12)
    ).all()

    return {
        "event_count": int(event_count),
        "historical_snapshot_count": int(historical_count),
        "window_stats": [
            {
                "window_type": row.window_type,
                "count": int(row.count),
                "avg_rv_ratio": float(row.avg_rv_ratio or 0.0),
                "avg_breakout_distance": float(row.avg_breakout_distance or 0.0),
                "avg_ret_20d": float(row.avg_ret_20d or 0.0),
                "avg_atr_pct": float(row.avg_atr_pct or 0.0),
            }
            for row in window_rows
        ],
        "top_quality_events": [
            {
                "ticker_id": event.ticker_id,
                "symbol": event.ticker.symbol if event.ticker else "-",
                "trigger_date": event.trigger_date.isoformat(),
                "peak_date": event.peak_date.isoformat(),
                "return_pct": float(event.return_pct),
                "duration_days": int(event.duration_days),
                "quality_score": float(event.event_quality_score),
            }
            for event in top_quality_events
        ],
    }
