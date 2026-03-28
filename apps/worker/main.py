import time

from packages.config import get_settings
from packages.db.session import SessionLocal
from packages.services.analysis import run_full_scan
from packages.services.bootstrap import bootstrap_universe
from packages.services.logging import configure_logging, get_logger

logger = get_logger(__name__)


def run_cycle() -> None:
    with SessionLocal() as db:
        bootstrap_universe(db)
        run = run_full_scan(db)
        logger.info("Completed scan run", extra={"run_id": run.id, "status": run.status})


def main() -> None:
    configure_logging()
    settings = get_settings()
    logger.info("Starting worker loop")
    while True:
        logger.info("Starting worker cycle")
        run_cycle()
        logger.info("Sleeping until next worker cycle")
        time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()
