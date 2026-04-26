import redis.asyncio as aioredis
import json
import os
from functools import wraps
from typing import Callable, Any

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DEFAULT_TTL = 3600  # 1 hour

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis


async def cache_get(key: str) -> Any | None:
    try:
        r = await get_redis()
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL):
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value))
    except Exception:
        pass


async def cache_bust(prefix: str):
    """Delete all cached keys that start with `prefix`. Safe to call when Redis is down."""
    try:
        r = await get_redis()
        keys = await r.keys(f"{prefix}*")
        if keys:
            await r.delete(*keys)
    except Exception:
        pass
