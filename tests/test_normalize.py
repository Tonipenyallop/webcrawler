import pytest

from webcrawler.normalize import normalize_url


@pytest.mark.parametrize("raw,expected", [
    # lowercase scheme+host ONLY — path case is preserved (paths are case-sensitive)
    ("HTTP://Example.com/About", "http://example.com/About"),
    ("http://example.com/about#team", "http://example.com/about"),  # drop fragment
    # strip trailing slash
    ("http://example.com/about/", "http://example.com/about"),
    # root path normalized to /
    ("http://example.com", "http://example.com/"),
    # drop default http port
    ("http://example.com:80/x", "http://example.com/x"),
    # drop default https port
    ("https://example.com:443/x", "https://example.com/x"),
    ("http://example.com/a?b=2", "http://example.com/a?b=2"),       # keep query
])
def test_normalize_canonical_forms(raw, expected):
    assert normalize_url(raw) == expected


def test_normalize_resolves_relative_against_base():
    assert normalize_url(
        "../foo", base="http://example.com/a/b/") == "http://example.com/a/foo"


def test_normalize_resolves_root_relative():
    assert normalize_url(
        "/x", base="http://example.com/a/b") == "http://example.com/x"
