from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base


class Ticker(Base):
    __tablename__ = "tickers"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    exchange: Mapped[str] = mapped_column(String(32), default="NASDAQ")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sector: Mapped[str | None] = mapped_column(String(128), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)

    daily_bars = relationship("DailyBar", back_populates="ticker", cascade="all, delete-orphan")
    pump_events = relationship("PumpEvent", back_populates="ticker", cascade="all, delete-orphan")
    feature_snapshots = relationship(
        "FeatureSnapshot", back_populates="ticker", cascade="all, delete-orphan"
    )
    scan_results = relationship("ScanResult", back_populates="ticker", cascade="all, delete-orphan")

