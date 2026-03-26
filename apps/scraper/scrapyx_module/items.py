import scrapy


class ProductItem(scrapy.Item):
    url = scrapy.Field()
    source = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    rating = scrapy.Field()
    description = scrapy.Field()
    images = scrapy.Field()
