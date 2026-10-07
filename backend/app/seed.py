"""Idempotent demo fixtures: python -m app.seed. Never runs in web startup."""

import asyncio
from uuid import NAMESPACE_URL, uuid5

from app.config import Settings
from app.providers.cache import RedisCache
from app.providers.triage.rules import RuleBasedTriage
from app.repositories.complaints import ComplaintRepository
from app.repositories.database import make_engine, make_sessions

TEXTS = [
    "Water pipe burst since fajr, flooding is entering homes near the masjid",
    "Pani supply is missing for three days; families are buying tankers",
    "Streetlight outside the school has been off since jumma",
    "Street light flickers every evening near the bus stop",
    "Exposed wire is sparking near the transformer, children pass here",
    "Bijli is out every night for several hours in our block",
    "Kachra has not been collected this week beside the market",
    "Sewage drain is blocked and bad smell is reaching the shops",
    "Large pothole on the road makes rickshaws swerve into traffic",
    "Footpath tiles are broken outside the clinic, please repair",
    "Park bench paint is faded near the cricket ground",
    "Public playground gate is broken and needs maintenance",
]


async def main():
    settings = Settings()
    engine = make_engine(settings.database_url)
    cache = RedisCache(settings.redis_url)
    try:
        rows = []
        for index in range(36):
            text = TEXTS[index % len(TEXTS)]
            location = f"Sector {['G-9', 'I-10', 'F-8'][index // 12]}, Street {index + 1}, Islamabad"
            triage = await RuleBasedTriage().triage(text, location)
            rows.append(
                {
                    "id": uuid5(NAMESPACE_URL, f"civicpulse:seed:v1:{index}"),
                    "text": text,
                    "location": location,
                    "category": triage.category,
                    "priority": triage.priority,
                    "status": ["open", "in_progress", "resolved", "rejected"][index % 4],
                    "triaged_by": "rules",
                    "ai_summary": triage.summary,
                    "triage_latency_ms": 0,
                }
            )
        count = await asyncio.to_thread(ComplaintRepository(make_sessions(engine)).seed, rows)
        if count:
            await cache.increment("stats:version")
        print(f"Inserted {count} demo complaints (36 stable fixtures).")
    finally:
        await cache.close()
        engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
