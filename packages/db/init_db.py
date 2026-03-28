from sqlalchemy import text

from packages.db.base import Base
from packages.db.models import *  # noqa: F403
from packages.db.session import engine


def verify_database_connection() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def ensure_database_schema() -> None:
    Base.metadata.create_all(bind=engine)
