import redis.asyncio as redis
from typing import Optional

redis_client = redis.Redis()

async def set_token_rate(symbol: str, rate: float):
    await redis_client.set(symbol.upper(), rate)

async def get_token_rate(symbol: str) -> Optional[float]:
    value = await redis_client.get(symbol.upper())
    return float(value) if value else None