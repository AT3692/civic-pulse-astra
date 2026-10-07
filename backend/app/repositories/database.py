from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    kwargs = {"connect_args": {"connect_timeout": 3}} if url.startswith("postgresql") else {}
    return create_engine(url, pool_pre_ping=True, **kwargs)


def make_sessions(engine):
    return sessionmaker(engine, expire_on_commit=False)
