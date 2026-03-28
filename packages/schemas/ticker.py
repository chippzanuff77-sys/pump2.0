from pydantic import BaseModel, ConfigDict


class TickerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    exchange: str
    is_active: bool
    sector: str | None = None
    industry: str | None = None

