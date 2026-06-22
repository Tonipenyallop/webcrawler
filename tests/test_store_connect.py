from webcrawler.store import Store


async def test_connect_returns_a_store(db_dsn):
    # connect() builds and returns a Store (not a bare pool).
    store = await Store.connect(db_dsn)
    try:
        assert isinstance(store, Store)
    finally:
        await store.pool.close()


async def test_connect_pool_can_query_the_database(db_dsn):
    # The Store from connect() has a live, usable pool — a real query round-trips.
    store = await Store.connect(db_dsn)
    try:
        assert await store.pool.fetchval("SELECT 1") == 1
    finally:
        await store.pool.close()
