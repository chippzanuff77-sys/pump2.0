from datetime import datetime

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    ticker_count: int
    event_count: int
    latest_run_id: int | None = None
    latest_run_status: str | None = None
    latest_run_started_at: datetime | None = None
    latest_run_finished_at: datetime | None = None
    latest_run_candidates: int = 0
    top_score: float = 0.0

