from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base


class PumpEvent(Base):
    __tablename__ = "pump_events"
    __table_args__ = (Index("ix_pump_events_ticker_trigger", "ticker_id", "trigger_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id", ondelete="CASCADE"), index=True)
    base_date: Mapped[date] = mapped_column(Date)
    trigger_date: Mapped[date] = mapped_column(Date)
    peak_date: Mapped[date] = mapped_column(Date)
    base_price: Mapped[float] = mapped_column(Float)
    peak_price: Mapped[float] = mapped_column(Float)
    return_pct: Mapped[float] = mapped_column(Float)
    duration_days: Mapped[int]
    event_quality_score: Mapped[float] = mapped_column(Float)

    ticker = relationship("Ticker", back_populates="pump_events")
    feature_snapshots = relationship(
        "FeatureSnapshot", back_populates="event", cascade="all, delete-orphan"
    )
    pattern_snapshots = relationship(
        "PatternSnapshot", back_populates="event", cascade="all, delete-orphan"
    )
