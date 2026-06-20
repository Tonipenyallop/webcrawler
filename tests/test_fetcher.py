import httpx

from webcrawler.fetcher import Fetcher, FetchResult


def _mock_fetcher(handler):
    """A Fetcher whose network is replaced by an in-memory fake server (handler)."""
    f = Fetcher()
    f._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,   # mirror production so the redirect test works
    )
    return f


async def test_fetch_returns_status():
    # status_code is mapped onto FetchResult.status
    def handler(req):
        return httpx.Response(404, headers={"content-type": "text/html"}, text="")
    res = await _mock_fetcher(handler).fetch("http://example.com/")
    assert isinstance(res, FetchResult)
    assert res.status == 404


async def test_fetch_returns_body():
    # response text is mapped onto FetchResult.body
    def handler(req):
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<html>hi</html>")
    res = await _mock_fetcher(handler).fetch("http://example.com/")
    assert res.body == "<html>hi</html>"


async def test_fetch_normalizes_content_type():
    # "TEXT/HTML; charset=utf-8" → "text/html": strip params AND lowercase,
    # so the Worker can do a clean `content_type == "text/html"` check.
    def handler(req):
        return httpx.Response(200, headers={"content-type": "TEXT/HTML; charset=utf-8"}, text="")
    res = await _mock_fetcher(handler).fetch("http://example.com/")
    assert res.content_type == "text/html"


async def test_fetch_follows_redirect_and_records_final_url():
    # 302 → final_url reflects where we landed, not the original url.
    def handler(req):
        if req.url.path == "/start":
            return httpx.Response(302, headers={"location": "http://example.com/end"})
        return httpx.Response(200, headers={"content-type": "text/html"}, text="ok")
    res = await _mock_fetcher(handler).fetch("http://example.com/start")
    assert res.final_url == "http://example.com/end"
