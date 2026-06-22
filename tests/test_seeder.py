from webcrawler.frontier import Frontier
from webcrawler.seeder import seed

URL = "http://example.com/a"


# --- depth ---

async def test_seed_enqueues_url_at_depth_zero(redis_client):
    # Seeds are crawl entry points, so they go in at depth 0.
    f = Frontier(redis_client)
    await seed(f, [URL])
    assert await f.pop() == (URL, 0)


# --- coverage of the input ---

async def test_seed_enqueues_every_provided_seed(redis_client):
    # All seeds in the list reach the frontier (none dropped).
    f = Frontier(redis_client)
    await seed(f, ["http://example.com/a", "http://example.com/b"])
    popped = {await f.pop(), await f.pop()}
    assert popped == {("http://example.com/a", 0), ("http://example.com/b", 0)}


async def test_seed_preserves_seed_order(redis_client):
    # Seeds are enqueued in the order given (first listed is crawled first).
    f = Frontier(redis_client)
    await seed(f, ["http://example.com/a", "http://example.com/b"])
    assert await f.pop() == ("http://example.com/a", 0)
    assert await f.pop() == ("http://example.com/b", 0)


# --- edge cases ---

async def test_seed_empty_list_enqueues_nothing(redis_client):
    # No seeds → frontier stays empty, no crash.
    f = Frontier(redis_client)
    await seed(f, [])
    assert await f.pop() is None


async def test_seed_duplicate_seeds_enqueued_once(redis_client):
    # A repeated seed is deduped by the frontier — enqueued at most once.
    f = Frontier(redis_client)
    await seed(f, [URL, URL])
    assert await f.pop() == (URL, 0)
    assert await f.pop() is None


# --- return value ---

async def test_seed_returns_none(redis_client):
    # seed() is a side-effecting coroutine; it returns nothing.
    f = Frontier(redis_client)
    assert await seed(f, [URL]) is None
