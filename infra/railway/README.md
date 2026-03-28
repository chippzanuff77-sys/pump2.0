# Railway Setup

Create three Railway services from the same repository:

## API

`uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`

## Worker

`python -m apps.worker.main`

## Scheduler

`python -m apps.worker.scheduler`

Attach PostgreSQL and Redis, then set shared variables from `.env.example`.

