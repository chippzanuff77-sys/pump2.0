from apps.worker.main import run_cycle
from packages.services.logging import configure_logging, get_logger

logger = get_logger(__name__)


def main() -> None:
    configure_logging()
    logger.info("Starting scheduled job")
    run_cycle()


if __name__ == "__main__":
    main()
