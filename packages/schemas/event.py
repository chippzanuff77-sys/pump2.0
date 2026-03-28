from datetime import date

from pydantic import BaseModel, ConfigDict


class PumpEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker_id: int
    base_date: date
    trigger_date: date
    peak_date: date
    base_price: float
    peak_price: float
    return_pct: float
    duration_days: int
    event_quality_score: float

