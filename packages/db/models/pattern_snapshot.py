from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base


class PatternSnapshot(Base):
    __tablename__ = "pattern_snapshots"
    __table_args__ = (
        Index("ix_pattern_snapshots_kind_window", "snapshot_kind", "window_type"),
        Index("ix_pattern_snapshots_ticker_reference", "ticker_id", "reference_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("pump_events.id", ondelete="CASCADE"), nullable=True, index=True
    )
    reference_date: Mapped[date] = mapped_column(Date, index=True)
    snapshot_kind: Mapped[str] = mapped_column(String(24), index=True)
    window_type: Mapped[str] = mapped_column(String(24), index=True)
    ret_5d: Mapped[float] = mapped_column(Float, default=0.0)
    ret_10d: Mapped[float] = mapped_column(Float, default=0.0)
    ret_20d: Mapped[float] = mapped_column(Float, default=0.0)
    ret_30d: Mapped[float] = mapped_column(Float, default=0.0)
    rv_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    atr_pct: Mapped[float] = mapped_column(Float, default=0.0)
    volatility_10d: Mapped[float] = mapped_column(Float, default=0.0)
    range_compression_score: Mapped[float] = mapped_column(Float, default=0.0)
    breakout_distance: Mapped[float] = mapped_column(Float, default=0.0)
    rsi_14: Mapped[float] = mapped_column(Float, default=0.0)
    sma20_distance: Mapped[float] = mapped_column(Float, default=0.0)
    sma50_distance: Mapped[float] = mapped_column(Float, default=0.0)
    avg_dollar_volume_20d: Mapped[float] = mapped_column(Float, default=0.0)

    ticker = relationship("Ticker", back_populates="pattern_snapshots")
    event = relationship("PumpEvent", back_populates="pattern_snapshots")
