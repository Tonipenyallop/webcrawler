from webcrawler.store import Store


async def test_save_page_returns_id(pg_pool):
    # save_page inserts a row and returns its generated id.
    pid = await Store(pg_pool).save_page("http://example.com/a", 200, "text/html")
    assert isinstance(pid, int) and pid > 0


async def test_save_page_is_idempotent_on_url(pg_pool):
    # Saving the same url twice returns the SAME id (UNIQUE(url) → upsert, not a dupe row).
    store = Store(pg_pool)
    first = await store.save_page("http://example.com/a", 200, "text/html")
    second = await store.save_page("http://example.com/a", 200, "text/html")
    assert first == second


async def test_save_links_writes_one_row_per_link(pg_pool):
    # save_links writes one links row per target url, tied to the from-page id.
    store = Store(pg_pool)
    pid = await store.save_page("http://example.com/a", 200, "text/html")
    await store.save_links(pid, ["http://example.com/b", "http://example.com/c"])
    async with pg_pool.acquire() as conn:
        n = await conn.fetchval("SELECT count(*) FROM links WHERE from_page_id=$1", pid)
    assert n == 2


async def test_save_links_with_empty_list_is_a_noop(pg_pool):
    # No links → no rows written, no crash.
    store = Store(pg_pool)
    pid = await store.save_page("http://example.com/a", 200, "text/html")
    await store.save_links(pid, [])
    async with pg_pool.acquire() as conn:
        n = await conn.fetchval("SELECT count(*) FROM links WHERE from_page_id=$1", pid)
    assert n == 0
