from pydantic import BaseModel, ConfigDict


class TickerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    exchange: str
    is_active: bool
    sector: str | None = None
    industry: str | None = None


class TickerDetail(BaseModel):
    id: int
    symbol: str
    exchange: str
    is_active: bool
    sector: str | None = None
    industry: str | None = None
    bar_count: int = 0
    event_count: int = 0
