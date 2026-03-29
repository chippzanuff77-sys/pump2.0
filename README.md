# Historical Pump Scanner

Railway-ready MVP for scanning US stocks, cataloging historical x4 pump events, extracting pre-pump features, and ranking current tickers by similarity.

## Quick start

1. Copy `.env.example` to `.env`
2. Run `alembic upgrade head`
3. Start API with `uvicorn apps.api.main:app --host 0.0.0.0 --port 8000`

## Services

- `api`: FastAPI
- `worker`: long-running scan loop for Railway worker service
- `scheduler`: one-shot cron entrypoint for Railway cron job
