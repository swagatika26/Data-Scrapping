import json
import re
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.http import Response

from scrapyx_module.items import ProductItem


class UniversalProductSpider(scrapy.Spider):
    name = "universal_product"
    custom_settings = {"CONCURRENT_REQUESTS": 8, "DOWNLOAD_DELAY": 0.6}

    def __init__(self, url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url] if url else ["{paste_target_url_here}"]

    def parse(self, response: Response):
        for product in self._extract_jsonld_products(response):
            yield product
        any_cards = False
        for card in self._iter_product_cards(response):
            any_cards = True
            item = ProductItem(
                url=card.get("url") or response.url,
                source=urlparse(response.url).netloc,
                title=self._clean(card.get("title")),
                price=self._clean(card.get("price")),
                rating=self._clean(card.get("rating")),
                description=self._clean(card.get("description")),
                images=[urljoin(response.url, u) for u in card.get("images", []) if u],
            )
            yield item
        if not any_cards:
            single = self._extract_single_product(response)
            if single:
                yield single
        next_href = (
            response.css('a[rel="next"]::attr(href)').get()
            or response.css("li.next a::attr(href)").get()
            or response.xpath("//a[contains(., 'Next') or contains(., '›')]/@href").get()
        )
        if next_href:
            yield response.follow(next_href, callback=self.parse)

    def _clean(self, s):
        if not s:
            return None
        return re.sub(r"\s+", " ", s).strip()

    def _extract_jsonld_products(self, response: Response):
        scripts = response.css('script[type="application/ld+json"]::text').getall()
        for raw in scripts:
            try:
                data = json.loads(raw)
            except Exception:
                continue
            nodes = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for node in nodes:
                graph = node.get("@graph") if isinstance(node, dict) else None
                if isinstance(graph, list):
                    for g in graph:
                        yield from self._from_jsonld_obj(g, response)
                else:
                    yield from self._from_jsonld_obj(node, response)

    def _from_jsonld_obj(self, obj, response: Response):
        t = obj.get("@type") if isinstance(obj, dict) else None
        if isinstance(t, list):
            t = t[0] if t else None
        if t and str(t).lower() in {"product", "offer"}:
            title = obj.get("name") or obj.get("title")
            price = (obj.get("offers") or {}).get("price") if isinstance(obj.get("offers"), dict) else obj.get("price")
            rating = None
            ar = obj.get("aggregateRating")
            if isinstance(ar, dict):
                rating = ar.get("ratingValue") or ar.get("bestRating")
            desc = obj.get("description")
            images = []
            img = obj.get("image")
            if isinstance(img, list):
                images = img
            elif isinstance(img, str):
                images = [img]
            yield ProductItem(
                url=response.url,
                source=urlparse(response.url).netloc,
                title=title,
                price=str(price) if price is not None else None,
                rating=str(rating) if rating is not None else None,
                description=desc,
                images=[urljoin(response.url, u) for u in images if u],
            )

    def _iter_product_cards(self, response: Response):
        containers = response.css("article, li.product, div.product, div.s-result-item, div.search-result")
        for c in containers:
            title = c.css("h2 a::attr(title)").get() or c.css("h2 a::text").get() or c.css(".product-title::text, .title::text").get()
            price = c.css(".price::text, .product-price::text, .a-price .a-offscreen::text").get()
            rating = c.css(".rating::text, .stars::text, .a-icon-alt::text").get()
            description = c.css(".description::text, .desc::text").get()
            url = c.css("a::attr(href)").get()
            img = c.css("img::attr(src), img::attr(data-src), img::attr(data-original)").get()
            yield {
                "title": title,
                "price": price,
                "rating": rating,
                "description": description,
                "url": urljoin(response.url, url) if url else None,
                "images": [img] if img else [],
            }

    def _extract_single_product(self, response: Response):
        title = response.css("h1::text").get() or response.css("h1 .product-title::text").get() or response.css("meta[property='og:title']::attr(content)").get()
        price = response.css(".price::text, .product-price::text").get() or response.css("meta[itemprop='price']::attr(content)").get()
        rating = response.css(".rating::text, .stars::text").get() or response.css("meta[itemprop='ratingValue']::attr(content)").get()
        desc = response.css("#description::text, .description::text, .product-description::text").get() or " ".join(response.css("#description *::text, .description *::text").getall()[:50])
        images = response.css("img::attr(src), img::attr(data-src), img::attr(data-original)").getall()
        images = [urljoin(response.url, u) for u in images if u]
        if any([title, price, rating, desc, images]):
            return ProductItem(
                url=response.url,
                source=urlparse(response.url).netloc,
                title=self._clean(title),
                price=self._clean(price),
                rating=self._clean(rating),
                description=self._clean(desc),
                images=images[:10],
            )
        return None
