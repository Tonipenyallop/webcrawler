import logging
from dataclasses import dataclass
from webcrawler.frontier import Frontier
from webcrawler.fetcher import Fetcher
from webcrawler.parser import Parser
from webcrawler.store import Store
from webcrawler.config import CrawlConfig
from typing import Final

HTML_CONTENT_TYPE: Final = 'text/html'


@dataclass
class Worker:
    frontier: Frontier
    fetcher: Fetcher
    parser: Parser
    store: Store
    config: CrawlConfig

    # for testing
    async def run(self):
        count = self.config.max_pages
        while count > 0:
            is_ran = await self.run_once()
            if not is_ran:
                break
            count -= 1

    async def run_once(self) -> bool:
        """
            true -> I have worked
            false -> I have not worked(frontier was empty)
        """

        popped = await self.frontier.pop()
        if popped == None:
            return False

        url = popped[0]
        depth = popped[1]

        try:
            res = await self.fetcher.fetch(url=url)

            # check visited
            pid = await self.store.save_page(url=url, status=res.status, content_type=res.content_type)

            if res.content_type == HTML_CONTENT_TYPE:
                # only for html contents can have href
                links = self.parser.extract_links(res.final_url, res.body)
                await self.store.save_links(pid, links)

                for link in links:
                    if not self.config.is_allowed(link):
                        continue
                    if depth + 1 > self.config.max_depth:
                        continue

                    await self.frontier.add(link, depth + 1)

            return True

        except Exception:
            logging.exception(f"failed to fetch data with url:{url}")
            return True
