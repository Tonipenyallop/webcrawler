from dataclasses import dataclass
import json

from redis.asyncio import Redis


@dataclass
class Frontier:
    redis_client: Redis
    seen_key = 'seen'
    queue_key = 'frontier'

    async def add(self, url: str, val: int) -> bool:
        seen = await self.redis_client.sadd(self.seen_key, url) == 0
        if seen:
            return False

        await self.redis_client.rpush(self.queue_key, json.dumps([url, val]))

        return True

    async def pop(self) -> tuple[str, int]:
        popped = await self.redis_client.lpop(name=self.queue_key)

        if popped == None:
            return None

        return tuple(json.loads(popped))

    async def seen(self, url: str):
        return await self.redis_client.sismember(self.seen_key, url) == 1
