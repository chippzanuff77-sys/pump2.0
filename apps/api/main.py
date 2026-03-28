from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from apps.api.routes import dashboard, health, scans, tickers
from packages.config import get_settings
from packages.db.init_db import ensure_database_schema, verify_database_connection

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    verify_database_connection()
    ensure_database_schema()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="apps/api/static"), name="static")
app.include_router(dashboard.router)
app.include_router(health.router)
app.include_router(tickers.router, prefix="/api")
app.include_router(scans.router, prefix="/api")
