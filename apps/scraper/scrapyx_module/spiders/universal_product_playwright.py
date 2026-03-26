from urllib.parse import urlparse, urljoin
import scrapy
from scrapyx_module.items import ProductItem


class UniversalProductPlaywrightSpider(scrapy.Spider):
    name = "universal_product_playwright"
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        "CONCURRENT_REQUESTS": 8,
        "ROBOTSTXT_OBEY": False,
    }

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url] if url else ["{paste_target_url_here}"]

    def start_requests(self):
        for u in self.start_urls:
            yield scrapy.Request(u, meta={"playwright": True, "playwright_page_methods": [("wait_for_selector", "body")]})

    def parse(self, response):
        from scrapyx_module.spiders.universal_product import UniversalProductSpider

        helper = UniversalProductSpider()
        any_cards = False
        for card in helper._iter_product_cards(response):
            any_cards = True
            yield ProductItem(
                url=card.get("url") or response.url,
                source=urlparse(response.url).netloc,
                title=helper._clean(card.get("title")),
                price=helper._clean(card.get("price")),
                rating=helper._clean(card.get("rating")),
                description=helper._clean(card.get("description")),
                images=[urljoin(response.url, u) for u in card.get("images", []) if u],
            )
        if not any_cards:
            single = helper._extract_single_product(response)
            if single:
                yield single
        next_href = (
            response.css('a[rel="next"]::attr(href)').get()
            or response.css("li.next a::attr(href)").get()
            or response.xpath("//a[contains(., 'Next') or contains(., '›')]/@href").get()
        )
        if next_href:
            yield response.follow(next_href, callback=self.parse, meta={"playwright": True})
