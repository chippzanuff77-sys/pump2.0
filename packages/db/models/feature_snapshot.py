from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base


class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshots"
    __table_args__ = (Index("ix_feature_snapshots_ref_positive", "reference_date", "is_positive_case"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("pump_events.id", ondelete="CASCADE"), nullable=True, index=True
    )
    reference_date: Mapped[date] = mapped_column(Date, index=True)
    is_positive_case: Mapped[bool] = mapped_column(Boolean, default=False)
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

    ticker = relationship("Ticker", back_populates="feature_snapshots")
    event = relationship("PumpEvent", back_populates="feature_snapshots")

