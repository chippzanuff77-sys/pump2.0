from sqlalchemy import Float, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("scan_runs.id", ondelete="CASCADE"), index=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id", ondelete="CASCADE"), index=True)
    score: Mapped[float] = mapped_column(Float)
    similarity_score: Mapped[float] = mapped_column(Float)
    matched_pattern_count: Mapped[int] = mapped_column(Integer, default=0)
    explanation_json: Mapped[dict] = mapped_column(JSON, default=dict)

    run = relationship("ScanRun", back_populates="results")
    ticker = relationship("Ticker", back_populates="scan_results")
