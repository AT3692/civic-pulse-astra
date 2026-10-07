"""Init-container gate; reads schema version, never runs migrations."""

import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.repositories.database import make_engine


def main():
    engine = make_engine(Settings().database_url)
    try:
        for _ in range(150):
            try:
                with engine.connect() as connection:
                    if connection.scalar(text("SELECT version_num FROM alembic_version")) == "0001":
                        return
            except SQLAlchemyError:
                pass
            time.sleep(2)
        raise SystemExit("Schema not ready; inspect the civicpulse-migrate Job")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
