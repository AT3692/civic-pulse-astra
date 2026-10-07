"""Real PostgreSQL + Redis contracts. CI provides isolated services; never use a live DB."""

import asyncio
import os
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.config import Settings
from app.providers.cache import RedisCache
from app.providers.triage.simulated import SimulatedTriage
from app.repositories.complaints import ComplaintRepository
from app.repositories.database import make_engine, make_sessions
from app.schemas import ComplaintCreate
from app.services.complaints import ComplaintService
from app.services.triage import TriageService

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="Requires isolated PostgreSQL/Redis services"
)


@pytest.fixture
def database(monkeypatch):
    url = os.environ["TEST_DATABASE_URL"]
    # This suite deliberately exercises downgrade. Reject accidental production targets.
    if "civicpulse_test" not in url:
        raise RuntimeError("TEST_DATABASE_URL must name civicpulse_test")
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = make_engine(url)
    yield ComplaintRepository(make_sessions(engine)), engine, config
    engine.dispose()


async def test_real_postgres_redis_lifecycle(database):
    repo, engine, config = database
    cache = RedisCache(os.environ["TEST_REDIS_URL"])
    try:
        await cache.ping()
        svc = ComplaintService(repo, cache, TriageService(SimulatedTriage(), cache), Settings())
        item = await svc.create(
            ComplaintCreate(text="Water pipe burst flooding the road", location="G-9 Islamabad"), str(uuid4())
        )
        assert repo.get(item.id).id == item.id
        assert item.created_at.tzinfo is not None
        assert not await svc.ready()
        assert (await svc.stats())[1] == "MISS"
        assert (await svc.stats())[1] == "HIT"
        row = {**item.model_dump(exclude={"allowed_transitions", "created_at", "updated_at"}), "id": uuid4()}
        assert repo.seed([row]) == 1
        assert repo.seed([row]) == 0
        with pytest.raises(IntegrityError):
            repo.create({**row, "id": uuid4(), "text": "short"})
        # Versions and tables are removed only in this isolated CI database.
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM complaints")) == 0
    finally:
        await cache.close()


async def test_redis_atomic_rate_limit_and_expiry(database):
    cache = RedisCache(os.environ["TEST_REDIS_URL"])
    key = "test:rate:" + str(uuid4())
    try:
        results = await asyncio.gather(*(cache.rate_limit(key, 3) for _ in range(15)))
        assert sum(allowed for allowed, _ in results) == 3
        assert 0 < await cache.client.ttl(key) <= 60
        for index in range(25):
            await cache.record_outcome(str(index))
        assert len(await cache.outcomes()) == 20
        await cache.set("test:ttl", "value", 30)
        assert 0 < await cache.client.ttl("test:ttl") <= 30
    finally:
        await cache.delete(key)
        await cache.close()
