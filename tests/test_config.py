from webcrawler.config import CrawlConfig


def test_is_allowed_matches_domain():
    cfg = CrawlConfig(allowed_domains=frozenset({"example.com"}), max_depth=2, max_pages=100)
    assert cfg.is_allowed("http://example.com/a") is True
    assert cfg.is_allowed("http://other.com/a") is False


def test_is_allowed_is_case_insensitive_on_host():
    cfg = CrawlConfig(allowed_domains=frozenset({"example.com"}), max_depth=2, max_pages=100)
    assert cfg.is_allowed("http://EXAMPLE.com/a") is True
