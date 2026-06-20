import fakeredis.aioredis
import pytest_asyncio


@pytest_asyncio.fixture
async def redis_client():
    """A fresh in-memory fake Redis for each test (no real server needed)."""
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await client.flushall()
    yield client
    await client.aclose()
