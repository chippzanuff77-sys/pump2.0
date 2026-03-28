from sqlalchemy import text

from packages.db.session import engine


def verify_database_connection() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

