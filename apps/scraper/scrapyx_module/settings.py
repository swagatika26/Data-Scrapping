BOT_NAME = "scrapyx_module"

SPIDER_MODULES = ["scrapyx_module.spiders"]
NEWSPIDER_MODULE = "scrapyx_module.spiders"

CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 0.7
RANDOMIZE_DOWNLOAD_DELAY = True
RETRY_ENABLED = True
RETRY_TIMES = 3
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 8.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0

ROBOTSTXT_OBEY = False

DOWNLOADER_MIDDLEWARES = {
    "scrapyx_module.middlewares.RandomUserAgentMiddleware": 400,
    "scrapyx_module.middlewares.DefaultHeadersMiddleware": 450,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
}

ITEM_PIPELINES = {
    "scrapyx_module.pipelines.CleanAndExportPipeline": 300,
}

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

DOWNLOAD_TIMEOUT = 30
LOG_LEVEL = "INFO"
