import os
import asyncio

from webcrawler.worker import Worker
from webcrawler.frontier import Frontier
from webcrawler.fetcher import Fetcher
from webcrawler.parser import Parser
from webcrawler.store import Store
from webcrawler.config import CrawlConfig
import redis.asyncio as aioredis


async def main():
    db_dsn = os.environ["WEBCRAWLER_DB_URL"]
    redis = aioredis.from_url(os.environ.get(
        "WEBCRAWLER_REDIS_URL", "redis://localhost:6379"), decode_responses=True)

    frontier = Frontier(redis)

    store = await Store.connect(db_dsn)

    allowed_domain = os.environ.get(
        "WEBCRAWLER_ALLOWED_DOMAINS", 'localhost')
    config = CrawlConfig(
        allowed_domains=frozenset(allowed_domain.split(',')),
        max_depth=int(os.environ.get("WEBCRAWLER_MAX_DEPTH", "5")),
        max_pages=int(os.environ.get("WEBCRAWLER_MAX_PAGES", "1000")),
    )

    worker = Worker(frontier, Fetcher(), Parser(), store, config)

    while True:
        if not await worker.run_once():
            await asyncio.sleep(10.0)


if __name__ == "__main__":
    asyncio.run(main())
