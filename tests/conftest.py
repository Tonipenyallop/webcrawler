import os

import asyncpg
import fakeredis.aioredis
import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def redis_client():
    """A fresh in-memory fake Redis for each test (no real server needed)."""
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await client.flushall()
    yield client
    await client.aclose()


@pytest_asyncio.fixture
async def pg_pool():
    """A real Postgres pool. Skips the test if WEBCRAWLER_DB_URL isn't set (no DB running)."""
    dsn = os.environ.get("WEBCRAWLER_DB_URL")
    if not dsn:
        pytest.skip(
            "WEBCRAWLER_DB_URL not set; start Postgres + export WEBCRAWLER_DB_URL to run")
    pool = await asyncpg.create_pool(dsn)
    async with pool.acquire() as conn:
        with open("sql/schema.sql") as fh:
            # idempotent (CREATE ... IF NOT EXISTS)
            await conn.execute(fh.read())
        # clean slate per test
        await conn.execute("TRUNCATE links, pages RESTART IDENTITY")
    yield pool
    await pool.close()
