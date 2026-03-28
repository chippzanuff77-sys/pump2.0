from dataclasses import asdict, dataclass

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.core.feature_engine.extractor import FeatureExtractor
from packages.core.similarity.scorer import FEATURE_KEYS, euclidean_similarity
from packages.db.models import DailyBar, FeatureSnapshot, PumpEvent, Ticker


@dataclass
class SimilarCase:
    symbol: str
    trigger_date: str
    peak_date: str
    return_pct: float
    duration_days: int
    similarity_score: float
    quality_score: float


def bars_frame(db: Session, ticker_id: int) -> pd.DataFrame:
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


def get_ticker_or_404(db: Session, symbol: str) -> Ticker | None:
    return db.scalars(select(Ticker).where(Ticker.symbol == symbol.upper())).first()


def get_current_feature_snapshot(db: Session, ticker_id: int) -> dict[str, float] | None:
    extractor = FeatureExtractor()
    bars = bars_frame(db, ticker_id)
    if bars.empty:
        return None
    return extractor.extract(bars, bars.iloc[-1]["date"])


def get_similar_historical_cases(
    db: Session, ticker_id: int, current_features: dict[str, float] | None, limit: int = 8
) -> list[dict]:
    if current_features is None:
        return []

    snapshots = db.scalars(
        select(FeatureSnapshot)
        .where(FeatureSnapshot.is_positive_case.is_(True))
        .order_by(FeatureSnapshot.reference_date.desc())
    ).all()

    cases: list[SimilarCase] = []
    for snapshot in snapshots:
        if snapshot.ticker_id == ticker_id or snapshot.event is None or snapshot.ticker is None:
            continue
        historical_features = {key: getattr(snapshot, key) for key in FEATURE_KEYS}
        similarity = euclidean_similarity(current_features, historical_features)
        cases.append(
            SimilarCase(
                symbol=snapshot.ticker.symbol,
                trigger_date=snapshot.event.trigger_date.isoformat(),
                peak_date=snapshot.event.peak_date.isoformat(),
                return_pct=snapshot.event.return_pct,
                duration_days=snapshot.event.duration_days,
                similarity_score=similarity,
                quality_score=snapshot.event.event_quality_score,
            )
        )

    ranked = sorted(cases, key=lambda item: item.similarity_score, reverse=True)[:limit]
    return [asdict(case) for case in ranked]


def get_recent_events(db: Session, ticker_id: int, limit: int = 12) -> list[PumpEvent]:
    return db.scalars(
        select(PumpEvent)
        .where(PumpEvent.ticker_id == ticker_id)
        .order_by(PumpEvent.trigger_date.desc())
        .limit(limit)
    ).all()
