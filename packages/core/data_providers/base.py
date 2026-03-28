from abc import ABC, abstractmethod

import pandas as pd


class DailyBarProvider(ABC):
    @abstractmethod
    def fetch_daily_bars(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        raise NotImplementedError

