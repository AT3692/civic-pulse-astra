from typing import Protocol, cast

from redis.asyncio import Redis


class Cache(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def increment(self, key: str) -> int: ...
    async def rate_limit(self, key: str, limit: int) -> tuple[bool, int]: ...
    async def record_outcome(self, value: str) -> None: ...
    async def outcomes(self) -> list[str]: ...
    async def ping(self) -> None: ...
    async def close(self) -> None: ...


class RedisCache:
    def __init__(self, url: str):
        self.client = Redis.from_url(url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)

    async def get(self, key: str) -> str | None:
        return cast(str | None, await self.client.get(key))

    async def set(self, key: str, value: str, ttl: int) -> None:
        await self.client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def increment(self, key: str) -> int:
        return await self.client.incr(key)

    async def rate_limit(self, key: str, limit: int) -> tuple[bool, int]:
        # Increment and expiry are atomic; a crashed worker cannot leave an immortal key.
        result = await self.client.eval(
            """
            local n = redis.call('INCR', KEYS[1])
            if n == 1 then redis.call('EXPIRE', KEYS[1], 60) end
            return {n, redis.call('TTL', KEYS[1])}
        """,
            1,
            key,
        )
        return int(result[0]) <= limit, max(1, int(result[1]))

    async def record_outcome(self, value: str) -> None:
        async with self.client.pipeline(transaction=True) as pipe:
            pipe.lpush("triage:outcomes", value)
            pipe.ltrim("triage:outcomes", 0, 19)
            await pipe.execute()

    async def outcomes(self) -> list[str]:
        return cast(list[str], await self.client.lrange("triage:outcomes", 0, 19))

    async def ping(self) -> None:
        await self.client.ping()

    async def close(self) -> None:
        await self.client.aclose()
