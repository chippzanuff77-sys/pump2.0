from datetime import date

from pydantic import BaseModel


class DailyBarRead(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
