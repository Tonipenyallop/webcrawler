from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class CrawlConfig:
    allowed_domains: frozenset[str]
    max_depth: int
    max_pages: int

    def is_allowed(self, input_url: str) -> bool:
        url = urlsplit(input_url)
        return url.hostname in self.allowed_domains
