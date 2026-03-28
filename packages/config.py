from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="historical-pump-scanner", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    default_universe: str = Field(default="NVDA,TSLA,AMD,PLTR,SOFI", alias="DEFAULT_UNIVERSE")
    min_avg_dollar_volume: float = Field(default=500_000, alias="MIN_AVG_DOLLAR_VOLUME")
    pump_multiplier: float = Field(default=2.0, alias="PUMP_MULTIPLIER")
    pump_lookahead_days: int = Field(default=20, alias="PUMP_LOOKAHEAD_DAYS")
    pump_base_lookback_days: int = Field(default=60, alias="PUMP_BASE_LOOKBACK_DAYS")
    worker_poll_seconds: int = Field(default=3600, alias="WORKER_POLL_SECONDS")

    @property
    def universe_symbols(self) -> list[str]:
        return [symbol.strip().upper() for symbol in self.default_universe.split(",") if symbol.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
