import asyncio
import hashlib
import json
import logging
import random
import time
from uuid import UUID

import httpx
from pydantic import ValidationError
from redis.exceptions import RedisError

from app.observability import FALLBACKS, TRIAGE
from app.providers.cache import Cache
from app.providers.triage.base import TriageProvider
from app.providers.triage.rules import RuleBasedTriage
from app.schemas import Outcome, ProviderMeta, TriageResult

logger = logging.getLogger(__name__)


class TriageService:
    def __init__(self, provider: TriageProvider, cache: Cache, model: str = "", sleep=asyncio.sleep):
        self.provider, self.cache, self.model, self.sleep = provider, cache, model, sleep

    async def triage(self, text: str, location: str, complaint_id: UUID) -> tuple[TriageResult, str, int]:
        start = time.perf_counter()
        key = (
            "triage:v1:"
            + hashlib.sha256(
                json.dumps([self.provider.name, self.model, text.strip(), location.strip()]).encode()
            ).hexdigest()
        )
        fallback, hit, result = False, False, None
        name = self.provider.name
        try:
            await self.cache.increment("triage:requests")
            raw = await self.cache.get(key)
            if raw:
                result = TriageResult.model_validate_json(raw)
                hit = True
                await self.cache.increment("triage:hits")
        except (RedisError, ValidationError):
            result, hit = None, False
        if result is None:
            try:
                for attempt in range(2):
                    try:
                        async with asyncio.timeout(10):
                            result = TriageResult.model_validate(await self.provider.triage(text, location))
                        break
                    except (TimeoutError, httpx.TimeoutException, httpx.HTTPStatusError) as error:
                        retryable = (
                            not isinstance(error, httpx.HTTPStatusError)
                            or error.response.status_code == 429
                            or error.response.status_code >= 500
                        )
                        if attempt or not retryable:
                            raise
                        await self.sleep(random.uniform(0.05, 0.25))
            except Exception as error:
                fallback, name = True, "rules:fallback"
                result = await RuleBasedTriage().triage(text, location)
                FALLBACKS.labels(self.provider.name).inc()
                logger.warning(
                    "triage_fallback",
                    extra={
                        "complaint_id": str(complaint_id),
                        "provider": self.provider.name,
                        "error_class": type(error).__name__,
                    },
                )
            if not fallback and result is not None:
                try:
                    await self.cache.set(key, result.model_dump_json(), 86400)
                except RedisError:
                    pass
        assert result is not None
        latency = int((time.perf_counter() - start) * 1000)
        TRIAGE.labels(name).observe(latency / 1000)
        try:
            await self.cache.record_outcome(
                Outcome(provider=name, latency_ms=latency, fallback=fallback, cache_hit=hit).model_dump_json()
            )
        except RedisError:
            pass
        return result, name, latency

    async def meta(self) -> ProviderMeta:
        hits = int(await self.cache.get("triage:hits") or 0)
        requests = int(await self.cache.get("triage:requests") or 0)
        return ProviderMeta(
            active_provider=self.provider.name,
            outcomes=[Outcome.model_validate_json(item) for item in await self.cache.outcomes()],
            triage_cache_hits=hits,
            triage_cache_requests=requests,
            triage_cache_hit_rate=hits / requests if requests else 0,
        )
