import asyncpg
from dataclasses import dataclass
import json


@dataclass
class Store:
    pool: asyncpg.Pool

    async def save_page(self, url: str, status: int, content_type: str) -> int:
        query = """
        INSERT INTO pages (url, status, content_type ) VALUES ($1, $2, $3)
        ON CONFLICT (url)
        DO UPDATE SET status = EXCLUDED.status, content_type = EXCLUDED.content_type
        RETURNING id;
        """

        id = await self.pool.fetchval(query, url, status, content_type)

        return id

    async def save_links(self, id: int, links: list[str]) -> None:

        query = """
        INSERT INTO links (from_page_id, to_url ) VALUES ($1,$2)
        RETURNING from_page_id
        """

        await self.pool.executemany(query, [(id, link) for link in links])
