from webcrawler.parser import Parser

BASE = "http://example.com/dir/page"


def test_extracts_and_resolves_links():
    html = '<a href="/a">A</a> <a href="rel">B</a> <a href="http://other.com/x">C</a>'
    links = Parser().extract_links(BASE, html)
    assert "http://example.com/a" in links           # root-relative
    assert "http://example.com/dir/rel" in links      # path-relative to BASE
    assert "http://other.com/x" in links              # absolute, external


def test_ignores_anchors_without_href():
    html = '<a>no href</a><a href="">empty</a><a href="/ok">ok</a>'
    assert Parser().extract_links(BASE, html) == ["http://example.com/ok"]


def test_dedupes_within_page():
    html = '<a href="/a">1</a><a href="/a#frag">2</a>'   # both normalize to the same URL
    assert Parser().extract_links(BASE, html) == ["http://example.com/a"]


def test_malformed_html_does_not_crash():
    assert Parser().extract_links(BASE, "<a href=/x>broken<<<") == ["http://example.com/x"]
