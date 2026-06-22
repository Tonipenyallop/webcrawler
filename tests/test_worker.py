import httpx

from webcrawler.config import CrawlConfig
from webcrawler.fetcher import Fetcher
from webcrawler.frontier import Frontier
from webcrawler.parser import Parser
from webcrawler.worker import Worker


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


def _fetcher_from_pages(pages: dict[str, str], content_type: str = "text/html") -> Fetcher:
    """Serve an inline {path: html} site; 404 for unknown paths."""
    def handler(req):
        html = pages.get(req.url.path)
        if html is None:
            return httpx.Response(404)
        return httpx.Response(200, headers={"content-type": content_type}, text=html)
    f = Fetcher()
    f._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), follow_redirects=True)
    return f


def _worker(frontier, fetcher, store, *, max_depth=5, max_pages=100) -> Worker:
    cfg = CrawlConfig(allowed_domains=frozenset(
        {"site.local"}), max_depth=max_depth, max_pages=max_pages)
    return Worker(frontier, fetcher, Parser(), store, cfg)


# --- return value: the daemon's work/no-work signal ---

async def test_run_once_empty_frontier_returns_false(redis_client):
    # Nothing queued → False, telling the daemon loop to sleep and poll.
    worker = _worker(Frontier(redis_client), _fetcher_from_pages({}), FakeStore())
    assert await worker.run_once() is False


async def test_run_once_with_queued_url_returns_true(redis_client):
    # A queued URL was processed → True, telling the daemon to keep going.
    frontier = Frontier(redis_client)
    await frontier.add("http://site.local/p", 0)
    worker = _worker(frontier, _fetcher_from_pages({"/p": ""}), FakeStore())
    assert await worker.run_once() is True


# --- exactly one URL per call ---

async def test_run_once_processes_exactly_one_url(redis_client):
    # Two URLs queued, one call → only one page is saved (the call drains one item).
    frontier = Frontier(redis_client)
    await frontier.add("http://site.local/a", 0)
    await frontier.add("http://site.local/b", 0)
    store = FakeStore()
    worker = _worker(frontier, _fetcher_from_pages({"/a": "", "/b": ""}), store)

    await worker.run_once()

    assert len(store.pages) == 1


# --- side effects of processing one URL ---

async def test_run_once_saves_the_fetched_page(redis_client):
    # The popped URL is recorded in the store.
    frontier = Frontier(redis_client)
    await frontier.add("http://site.local/p", 0)
    store = FakeStore()
    worker = _worker(frontier, _fetcher_from_pages({"/p": ""}), store)

    await worker.run_once()

    assert "http://site.local/p" in store.pages


async def test_run_once_enqueues_in_domain_links(redis_client):
    # An in-domain link discovered on the page is enqueued at depth+1.
    frontier = Frontier(redis_client)
    await frontier.add("http://site.local/p0", 0)
    pages = {"/p0": '<a href="p1">1</a>', "/p1": ""}
    worker = _worker(frontier, _fetcher_from_pages(pages), FakeStore())

    await worker.run_once()

    assert await frontier.pop() == ("http://site.local/p1", 1)


async def test_run_once_does_not_enqueue_external_links(redis_client):
    # A link outside allowed_domains is filtered out — never enqueued.
    frontier = Frontier(redis_client)
    await frontier.add("http://site.local/p0", 0)
    pages = {"/p0": '<a href="http://external.com/x">ext</a>'}
    worker = _worker(frontier, _fetcher_from_pages(pages), FakeStore())

    await worker.run_once()

    assert await frontier.pop() is None


async def test_run_once_does_not_enqueue_beyond_max_depth(redis_client):
    # With max_depth=0, a link discovered at depth 0 (would be depth 1) is not enqueued.
    frontier = Frontier(redis_client)
    await frontier.add("http://site.local/p0", 0)
    pages = {"/p0": '<a href="p1">1</a>', "/p1": ""}
    worker = _worker(frontier, _fetcher_from_pages(pages), FakeStore(), max_depth=0)

    await worker.run_once()

    assert await frontier.pop() is None


# --- resilience ---

async def test_run_once_returns_true_when_fetch_fails(redis_client):
    # A failing fetch is swallowed (logged) — the call still reports work was
    # consumed so the daemon loop keeps running instead of dying.
    def handler(req):
        raise httpx.ConnectError("simulated network failure")
    f = Fetcher()
    f._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    frontier = Frontier(redis_client)
    await frontier.add("http://site.local/bad", 0)
    worker = _worker(frontier, f, FakeStore())

    assert await worker.run_once() is True
