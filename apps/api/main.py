from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.routes import health, scans, tickers
from packages.config import get_settings
from packages.db.init_db import verify_database_connection

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    verify_database_connection()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(tickers.router, prefix="/api")
app.include_router(scans.router, prefix="/api")

