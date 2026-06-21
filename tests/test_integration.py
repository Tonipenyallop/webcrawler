import pathlib

import httpx

from webcrawler.config import CrawlConfig
from webcrawler.fetcher import Fetcher
from webcrawler.frontier import Frontier
from webcrawler.parser import Parser
from webcrawler.worker import Worker

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "site"


class FakeStore:
    """In-memory stand-in for Store so these tests need no Postgres."""

    def __init__(self):
        self.pages: dict[str, int] = {}
        self.links: list[tuple[int, str]] = []

    async def save_page(self, url, status, content_type) -> int:
        self.pages.setdefault(url, len(self.pages) + 1)
        return self.pages[url]

    async def save_links(self, from_page_id, to_urls) -> None:
        self.links += [(from_page_id, u) for u in to_urls]


def _fetcher(handler) -> Fetcher:
    """A Fetcher whose network is replaced by an in-memory fake server (handler)."""
    f = Fetcher()
    f._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)
    return f


def _fetcher_from_pages(pages: dict[str, str], content_type: str = "text/html") -> Fetcher:
    """Serve an inline {path: html} site; 404 for unknown paths."""
    def handler(req):
        html = pages.get(req.url.path)
        if html is None:
            return httpx.Response(404)
        return httpx.Response(200, headers={"content-type": content_type}, text=html)
    return _fetcher(handler)


def _fixture_fetcher() -> Fetcher:
    """Serve the local fixture-site files."""
    def handler(req):
        name = req.url.path.lstrip("/") or "index.html"
        path = FIXTURES / name
        if not path.exists():
            return httpx.Response(404)
        return httpx.Response(200, headers={"content-type": "text/html"}, text=path.read_text())
    return _fetcher(handler)


def _worker(frontier, fetcher, store, *, max_depth=5, max_pages=100) -> Worker:
    cfg = CrawlConfig(allowed_domains=frozenset({"site.local"}), max_depth=max_depth, max_pages=max_pages)
    return Worker(frontier, fetcher, Parser(), store, cfg)


# --- happy path ---

async def test_crawl_fixture_site(redis_client):
    # All three internal pages get crawled; the external link is filtered out.
    frontier = Frontier(redis_client)
    store = FakeStore()
    await frontier.add("http://site.local/index.html", 0)

    await _worker(frontier, _fixture_fetcher(), store).run()

    assert set(store.pages) == {
        "http://site.local/index.html",
        "http://site.local/a.html",
        "http://site.local/b.html",
    }
    assert not any("external.com" in u for u in store.pages)


async def test_crawl_respects_max_pages(redis_client):
    # With a cap of 1, only the seed is crawled even though it links to more.
    frontier = Frontier(redis_client)
    store = FakeStore()
    await frontier.add("http://site.local/index.html", 0)

    await _worker(frontier, _fixture_fetcher(), store, max_pages=1).run()

    assert len(store.pages) == 1


# --- depth enforcement ---

async def test_crawl_skips_pages_beyond_max_depth(redis_client):
    # Linear chain p0->p1->p2->p3. With max_depth=1, only p0 (depth 0) and
    # p1 (depth 1) are crawled; p2 (depth 2) is too deep and never fetched.
    pages = {
        "/p0": '<a href="p1">1</a>',
        "/p1": '<a href="p2">2</a>',
        "/p2": '<a href="p3">3</a>',
        "/p3": "",
    }
    frontier = Frontier(redis_client)
    store = FakeStore()
    await frontier.add("http://site.local/p0", 0)

    await _worker(frontier, _fetcher_from_pages(pages), store, max_depth=1).run()

    assert set(store.pages) == {"http://site.local/p0", "http://site.local/p1"}


# --- content-type handling ---

async def test_non_html_page_is_saved_but_not_parsed(redis_client):
    # A PDF response is recorded as a page, but its body is NOT parsed for links,
    # so the link inside it is never followed.
    pages = {"/doc": '<a href="other">should NOT be crawled</a>', "/other": ""}
    frontier = Frontier(redis_client)
    store = FakeStore()
    await frontier.add("http://site.local/doc", 0)

    await _worker(frontier, _fetcher_from_pages(pages, content_type="application/pdf"), store).run()

    assert set(store.pages) == {"http://site.local/doc"}   # /other was never followed


# --- resilience ---

async def test_one_failing_fetch_does_not_stop_the_crawl(redis_client):
    # index links to bad (which raises on fetch) and good. The crawl must log the
    # failure and continue — good still gets crawled.
    def handler(req):
        if req.url.path == "/bad":
            raise httpx.ConnectError("simulated network failure")
        html = {
            "/index": '<a href="bad">bad</a> <a href="good">good</a>',
            "/good": "",
        }.get(req.url.path)
        if html is None:
            return httpx.Response(404)
        return httpx.Response(200, headers={"content-type": "text/html"}, text=html)

    frontier = Frontier(redis_client)
    store = FakeStore()
    await frontier.add("http://site.local/index", 0)

    await _worker(frontier, _fetcher(handler), store).run()

    assert "http://site.local/index" in store.pages
    assert "http://site.local/good" in store.pages    # survived the failing /bad fetch
