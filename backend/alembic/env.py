from alembic import context
from app.config import Settings
from app.repositories import models  # noqa: F401
from app.repositories.database import Base, make_engine

target_metadata = Base.metadata
if context.is_offline_mode():
    context.configure(
        url=Settings().database_url.replace("postgresql://", "postgresql+psycopg://", 1),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(Settings().database_url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
