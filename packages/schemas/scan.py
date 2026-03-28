from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TriggerScanResponse(BaseModel):
    run_id: int | None = None
    status: str
    message: str


class ScanRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    tickers_scanned: int
    candidates_found: int


class ScanResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    ticker_id: int
    score: float
    similarity_score: float
    matched_pattern_count: int
    explanation_json: dict


class ScanResultWithTicker(ScanResultRead):
    symbol: str
