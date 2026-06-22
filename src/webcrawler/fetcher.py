from dataclasses import dataclass, field
import httpx

from typing import Final


TIME_OUT_IN_SEC: Final = 10.0


@dataclass
class FetchResult:
    status: int
    body: str
    content_type: str
    final_url: str


@dataclass
class Fetcher:
    _client: httpx.AsyncClient = field(default_factory=lambda: httpx.AsyncClient(
        follow_redirects=True, timeout=TIME_OUT_IN_SEC))

    async def fetch(self, url) -> FetchResult:
        res = await self._client.get(url)
        content_type = res.headers.get('content-type', '').split(';')[
            0].strip().lower()
        res_url = str(res.url)
        return FetchResult(res.status_code, res.text, content_type, res_url)
