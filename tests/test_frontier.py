import asyncio

from webcrawler.frontier import Frontier

URL = "http://example.com/a"


# --- add: return value ---

async def test_add_new_url_returns_true(redis_client):
    # A never-seen url is newly added → True.
    assert await Frontier(redis_client).add(URL, 0) is True


async def test_add_duplicate_returns_false(redis_client):
    # Adding the same url again is rejected → False.
    f = Frontier(redis_client)
    await f.add(URL, 0)
    assert await f.add(URL, 0) is False


# --- add: side effects ---

async def test_add_records_url_in_seen_set(redis_client):
    # add() must mark the url in the dedup set (observable via seen()).
    f = Frontier(redis_client)
    await f.add(URL, 0)
    assert await f.seen(URL) is True


async def test_add_enqueues_url_with_its_depth(redis_client):
    # add() must enqueue the [url, depth] pair (observable via pop()).
    f = Frontier(redis_client)
    await f.add(URL, 2)
    assert await f.pop() == (URL, 2)


async def test_duplicate_add_enqueues_only_once(redis_client):
    # The dedup gate means a repeated url is enqueued at most once.
    f = Frontier(redis_client)
    await f.add(URL, 0)
    await f.add(URL, 0)
    assert await f.pop() == (URL, 0)
    assert await f.pop() is None


# --- pop ---

async def test_pop_is_fifo_order(redis_client):
    # First url added comes out first (catches LIFO bugs like list.pop()).
    f = Frontier(redis_client)
    await f.add("http://example.com/a", 0)
    await f.add("http://example.com/b", 1)
    assert await f.pop() == ("http://example.com/a", 0)
    assert await f.pop() == ("http://example.com/b", 1)


async def test_pop_empty_returns_none(redis_client):
    # Empty queue → None, no crash.
    assert await Frontier(redis_client).pop() is None


# --- seen ---

async def test_seen_is_false_for_unknown_url(redis_client):
    # seen() is a read-only check; an unknown url is not present.
    assert await Frontier(redis_client).seen(URL) is False


# --- concurrency ---

async def test_concurrent_add_enqueues_exactly_once(redis_client):
    # The race test: 50 workers add the same url at once; the atomic SADD means
    # exactly one wins (returns True) — proving distributed dedup correctness.
    f = Frontier(redis_client)
    results = await asyncio.gather(*[f.add(URL, 0) for _ in range(50)])
    assert sum(results) == 1
