from dataclasses import dataclass
import httpx

from typing import Final


TIME_OUT_IN_SEC: Final = 10.0


@dataclass
class FetchResult:
    status: int
    body: str
    content_type: str
    final_url: str


class Fetcher:
    def __init__(self):
        self._client = httpx.AsyncClient(
            follow_redirects=True, timeout=TIME_OUT_IN_SEC)

    async def fetch(self, url) -> FetchResult:
        res = await self._client.get(url)
        content_type = res.headers.get('content-type', '').split(';')[
            0].strip().lower()
        res_url = str(res.url)
        return FetchResult(res.status_code, res.text, content_type, res_url)
