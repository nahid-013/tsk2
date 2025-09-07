BOT_NAME = 'alkoteka_scraper'

SPIDER_MODULES = ['alkoteka_scraper.spiders']
NEWSPIDER_MODULE = 'alkoteka_scraper.spiders'

# Crawl responsibly
ROBOTSTXT_OBEY = False

USER_AGENT = 'Mozilla/5.0 (compatible; AlkotekaScraper/1.0; +https://example.com)'
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 0.5

# Enable proxy middleware
DOWNLOADER_MIDDLEWARES = {
    'alkoteka_scraper.middlewares.ProxyMiddleware': 350,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

# Logging
LOG_LEVEL = 'INFO'
