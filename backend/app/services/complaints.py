import asyncio
import hashlib
import secrets
from uuid import UUID

from redis.exceptions import RedisError

from app.config import Settings
from app.providers.cache import Cache
from app.repositories.complaints import ComplaintRepository
from app.schemas import Category, Complaint, ComplaintCreate, ComplaintPage, Priority, Stats, Status
from app.services.errors import ServiceError
from app.services.triage import TriageService

TRANSITIONS: dict[Status, list[Status]] = {
    Status.open: [Status.in_progress, Status.rejected],
    Status.in_progress: [Status.resolved, Status.rejected],
    Status.resolved: [],
    Status.rejected: [],
}


def present(item: Complaint) -> Complaint:
    # Contact is stored privately; never include it in public dashboard responses.
    return item.model_copy(update={"allowed_transitions": TRANSITIONS[item.status], "reporter_contact": None})


class ComplaintService:
    def __init__(self, repo: ComplaintRepository, cache: Cache, triage: TriageService, settings: Settings):
        self.repo, self.cache, self.triage, self.settings = repo, cache, triage, settings

    def authorize_operator(self, token: str) -> None:
        expected = self.settings.operator_api_key.get_secret_value()
        if expected and not secrets.compare_digest(token, expected):
            raise ServiceError(401, "A valid operator key is required")

    async def create(self, data: ComplaintCreate, client_ip: str) -> Complaint:
        key = "rate:" + hashlib.sha256(client_ip.encode()).hexdigest()
        try:
            allowed, retry = await self.cache.rate_limit(key, self.settings.rate_limit_per_minute)
        except RedisError as error:
            raise ServiceError(503, "Rate limiter unavailable; retry shortly", {"Retry-After": "5"}) from error
        if not allowed:
            raise ServiceError(429, "Submission rate limit exceeded", {"Retry-After": str(retry)})
        complaint_id = await asyncio.to_thread(self.repo.new_id)
        result, provider, latency = await self.triage.triage(data.text, data.location, complaint_id)
        item = await asyncio.to_thread(
            self.repo.create,
            {
                **data.model_dump(),
                "id": complaint_id,
                "category": result.category,
                "priority": result.priority,
                "ai_summary": result.summary,
                "triaged_by": provider,
                "triage_latency_ms": latency,
            },
        )
        await self.invalidate()
        return present(item)

    async def get(self, complaint_id: UUID) -> Complaint:
        item = await asyncio.to_thread(self.repo.get, complaint_id)
        if item is None:
            raise ServiceError(404, "Complaint not found")
        return present(item)

    async def list_complaints(
        self, page: int, page_size: int, category: Category | None, priority: Priority | None, status: Status | None
    ) -> ComplaintPage:
        items, total = await asyncio.to_thread(self.repo.list_complaints, page, page_size, category, priority, status)
        return ComplaintPage(items=[present(item) for item in items], total=total, page=page, page_size=page_size)

    async def transition(self, complaint_id: UUID, target: Status) -> Complaint:
        current = await self.get(complaint_id)
        if target not in TRANSITIONS[current.status]:
            raise ServiceError(409, f"Invalid status transition: {current.status} → {target}")
        item = await asyncio.to_thread(self.repo.transition, complaint_id, current.status, target)
        if item is None:
            raise ServiceError(
                409, f"Concurrent status change prevented transition: {current.status} → {target}; refresh and retry"
            )
        await self.invalidate()
        return present(item)

    async def invalidate(self) -> None:
        try:
            await self.cache.increment("stats:version")
        except RedisError:
            # Committed writes still return success; cache outage means reads bypass cache.
            pass

    async def stats(self) -> tuple[Stats, str]:
        # Generation keys prevent a slow concurrent cache fill from resurrecting stale data.
        try:
            generation = await self.cache.get("stats:version") or "0"
            key = "stats:v1:" + generation
            raw = await self.cache.get(key)
            if raw:
                return Stats.model_validate_json(raw), "HIT"
        except RedisError:
            key = None
        stats = await asyncio.to_thread(self.repo.stats)
        if key:
            try:
                await self.cache.set(key, stats.model_dump_json(), 30)
            except RedisError:
                pass
        return stats, "MISS"

    async def ready(self) -> list[str]:
        results = await asyncio.gather(asyncio.to_thread(self.repo.ping), self.cache.ping(), return_exceptions=True)
        return [
            name
            for name, result in zip(("postgres", "redis"), results, strict=True)
            if isinstance(result, BaseException)
        ]
