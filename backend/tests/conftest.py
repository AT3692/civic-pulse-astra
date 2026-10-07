from collections import deque

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.main import create_app
from app.providers.triage.simulated import SimulatedTriage
from app.repositories.complaints import ComplaintRepository
from app.repositories.database import Base, make_sessions
from app.services.complaints import ComplaintService
from app.services.triage import TriageService


class MemoryCache:
    def __init__(self):
        self.values = {}
        self.history = deque(maxlen=20)
        self.ttls = {}
        self.failed = False

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ttl):
        self.values[key] = value
        self.ttls[key] = ttl

    async def delete(self, key):
        self.values.pop(key, None)

    async def increment(self, key):
        self.values[key] = str(int(self.values.get(key, 0)) + 1)
        return int(self.values[key])

    async def rate_limit(self, key, limit):
        return (await self.increment(key)) <= limit, 60

    async def record_outcome(self, value):
        self.history.appendleft(value)

    async def outcomes(self):
        return list(self.history)

    async def ping(self):
        if self.failed:
            raise ConnectionError("redis down")

    async def close(self):
        pass


@pytest.fixture
def stack():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)  # Isolated unit-test database only; deployment always uses Alembic.
    cache = MemoryCache()
    settings = Settings(rate_limit_per_minute=100, triage_provider="simulated")
    repo = ComplaintRepository(make_sessions(engine))
    triage = TriageService(SimulatedTriage(), cache)
    svc = ComplaintService(repo, cache, triage, settings)
    with TestClient(create_app(settings, svc)) as client:
        yield client, svc, cache
    engine.dispose()
