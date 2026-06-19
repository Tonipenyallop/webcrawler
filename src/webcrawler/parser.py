from selectolax.parser import HTMLParser
from webcrawler.normalize import normalize_url


class Parser:
    def __init__(self):
        pass

    def extract_links(self, base: str, html: str) -> list[str]:

        outSet = set()

        parser = HTMLParser(html=html)
        nodes = parser.css('a[href]')

        for node in nodes:
            href = node.attributes['href']
            if href == None:
                continue

            url = normalize_url(url=href, base=base)
            outSet.add(url)

        return list(outSet)
