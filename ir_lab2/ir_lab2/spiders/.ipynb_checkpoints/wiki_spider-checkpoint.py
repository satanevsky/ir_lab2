import scrapy
from bs4 import BeautifulSoup
from ir_lab2.items import IrLab2Item

import re

class WikiSpider(scrapy.Spider):
    name = 'wiki'
    start_urls = [
        'https://en.wikipedia.org/wiki/Logistic_regression',
        'https://en.wikipedia.org/wiki/PageRank',
        'https://en.wikipedia.org/wiki/Python_(programming_language)',
    ]

    # we have two sets to not have duplicate links in downloaded queue
    seen_urls = set()
    queued_urls = set()

    header_selector = 'h1#firstHeading.firstHeading::text'
    body_link_selector = '(//div[@id="mw-content-text"]/p/a/@href)[position() < 100]'
    allowed_re = re.compile('https://en\.wikipedia\.org/wiki/'
                            '(?!((File|Talk|Category|Portal|Special|'
                            'Template|Template_talk|Wikipedia|Help|Draft):|Main_Page)).+')

    def _prepare_allowed_links(self, response, links):
        ans = list()
        for link in links:
            if link[0] == '#':
                continue
            next_url = response.urljoin(link)
            if self.allowed_re.match(next_url):
                ans.append(next_url)
        return ans

    def _yield_links_to_be_downloaded(self, links):
        for link in links:
            if link not in self.seen_urls and link not in self.queued_urls:
                self.queued_urls.add(link)
                yield link

    def parse(self, response):
        item = IrLab2Item()        
        item['title'] = response.css(self.header_selector).extract_first()
        item['url'] = response.url
        item['snippet'] = BeautifulSoup(
            response.xpath('//div[@id="mw-content-text"]/p[1]').extract_first(),
            "lxml",
        ).text[:255] + "..."

        links = self._prepare_allowed_links(
            response=response,
            links=response.xpath(self.body_link_selector).extract(),
        )
        item['outgoing_links'] = links

        yield item

        self.seen_urls.add(response.url)
        if len(self.seen_urls) > 20000:
            raise scrapy.exceptions.CloseSpider('enough urls parsed')

        for next_url in self._yield_links_to_be_downloaded(links):
            yield scrapy.Request(next_url, callback=self.parse)
