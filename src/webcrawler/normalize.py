from urllib.parse import urljoin, urlsplit, urlunsplit


def normalize_url(url: str, base: str | None = None) -> str:
    if base:
        url = urljoin(base, url)

    tmp = urlsplit(url)

    path = tmp.path or "/"

    # eg) http://example.com/about
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip('/')

    out = urlunsplit((tmp.scheme, tmp.hostname,
                      path, tmp.query, ""))

    return out
