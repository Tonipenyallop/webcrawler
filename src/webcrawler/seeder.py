
import os
import argparse
import asyncio

from webcrawler.frontier import Frontier

import redis.asyncio as aioredis


async def seed(frontier: Frontier, urls: list[str]) -> None:
    for url in urls:
        await frontier.add(url, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    # 1+ positional URLs → args.seeds is a list[str]
    parser.add_argument("seeds", nargs="+")
    parser.add_argument(
        "--redis-url", default=os.environ.get('REDIS_URL', "redis://localhost:6379"))

    args = parser.parse_args()

    _client = aioredis.from_url(args.redis_url, decode_responses=True)

    asyncio.run(seed(Frontier(_client), args.seeds))


if __name__ == "__main__":
    main()
