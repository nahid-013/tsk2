import scrapy
import time
import os
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
import json

class AlkotekaSpider(scrapy.Spider):
    name = 'alkoteka'
    custom_settings = {
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    # Option 1: read from start_urls.txt if exists, else fallback to START_URLS constant
    START_URLS = [
        'https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',
        'https://alkoteka.com/catalog/vino-1',
        'https://alkoteka.com/catalog/konjak-3',
    ]

    def start_requests(self):
        # Try reading external file start_urls.txt in project root
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        txt_path = os.path.join(base, 'start_urls.txt')
        urls = []
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                for line in f:
                    u = line.strip()
                    if not u or u.startswith('#'):
                        continue
                    urls.append(u)
        if not urls:
            urls = self.START_URLS

        # Set cookies/headers for region = Краснодар. If site uses different mechanism, adjust manually.
        cookies = {'region': 'Краснодар'}
        headers = {'Accept-Language': 'ru-RU,ru'}

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_category, cookies=cookies, headers=headers, meta={'start_url': url})

    def parse_category(self, response):
        # Parse product links on category page and follow pagination
        product_links = response.css('a.product-card__link::attr(href), a.product__link::attr(href)').getall()
        if not product_links:
            # fallback broad selector
            product_links = response.css('a::attr(href)').re(r'/product/[^/]+')  # best-effort
        for href in product_links:
            full = response.urljoin(href)
            yield scrapy.Request(full, callback=self.parse_product, meta={'start_url': response.meta.get('start_url')})

        # Pagination: try to find next page link
        next_page = response.css('a.pagination__next::attr(href), a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_category, meta=response.meta)
        else:
            # try page numbers pattern: look for ?PAGEN_1=2 or page=2 links
            for href in response.css('a::attr(href)').getall():
                if 'PAGEN' in href or 'page=' in href:
                    # rely on normal crawling to catch other pages
                    pass

    def _extract_price(self, response):
        # Try multiple selectors for prices (site-specific adjustments may be needed)
        # current price (sale) first
        curr = response.css('.price__current::text, .product-price__current::text, .js-price-current::text').get()
        orig = response.css('.price__old::text, .product-price__old::text, .js-price-original::text').get()
        def norm(text):
            if not text:
                return None
            t = text.strip().replace('\xa0', '').replace('₽','').replace('₽','').replace(',','.')
            try:
                return float(''.join([c for c in t if c.isdigit() or c=='.']))
            except:
                return None
        current = norm(curr) or norm(orig) or 0.0
        original = norm(orig) or current
        sale_tag = ''
        try:
            if original and original > 0 and original > current:
                discount = round((original - current) / original * 100)
                sale_tag = f"Скидка {discount}%"
        except Exception:
            sale_tag = ''
        return current, original, sale_tag

    def parse_product(self, response):
        timestamp = int(time.time())
        url = response.url
        # RPC: try to find SKU or article code on page; fallback to numeric id from URL
        rpc = response.css('.sku, .product-sku::text, .product__sku::text').re_first(r'\d+')
        if not rpc:
            # parse digits from URL
            rpc = ''.join(ch for ch in url if ch.isdigit())
            if not rpc:
                rpc = url

        # Title: if volume/color present in page separate, append to title
        title = response.css('h1::text, .product-title::text').get()
        if title:
            title = title.strip()
        # try to find volume/color
        vol = response.css('.product-volume::text, .volume::text, .sku-property::text').get()
        if vol:
            vol = vol.strip()
            if vol not in title:
                title = f"{title}, {vol}"

        # marketing tags: look for textual badges
        marketing = response.css('.badge::text, .product-label::text, .tag::text').getall()
        marketing = [m.strip() for m in marketing if m and m.strip()]

        # brand
        brand = response.css('.brand a::text, .product-brand::text, .brand::text').get()
        if brand:
            brand = brand.strip()

        # section / breadcrumbs
        sections = response.css('.breadcrumbs a::text, .breadcrumb__item a::text').getall()
        sections = [s.strip() for s in sections if s.strip()]

        # price data
        current, original, sale_tag = self._extract_price(response)
        price_data = {'current': current, 'original': original, 'sale_tag': sale_tag}

        # stock info
        # try to detect "В наличии" or stock count
        in_stock = False
        count = 0
        stock_text = ' '.join(response.css('body *::text').re(r'В наличии|в наличии|Нет в наличии|Осталось \d+'))
        if 'В наличии' in stock_text or 'в наличии' in stock_text:
            in_stock = True
        cnt = response.css('.stock-quantity::text, .product-stock::text').re_first(r'(\d+)')
        if cnt:
            try:
                count = int(cnt)
            except: 
                count = 0

        # assets
        main_image = response.css('.product-gallery img::attr(src), .main-photo img::attr(src)').get()
        set_images = response.css('.product-gallery img::attr(data-src), .product-gallery img::attr(src)').getall()
        set_images = [response.urljoin(u) for u in set_images if u]
        view360 = []  # site-specific: leave empty unless found
        video = response.css('video source::attr(src), .video-wrapper iframe::attr(src)').getall()

        assets = {
            'main_image': response.urljoin(main_image) if main_image else '',
            'set_images': set_images,
            'view360': view360,
            'video': video
        }

        # metadata: description and other key-value specs
        description = response.css('.product-description, .description, #description ::text').getall()
        description = ' '.join([d.strip() for d in description if d.strip()])

        metadata = {}
        if description:
            metadata['__description'] = description

        # try to extract spec table rows
        for row in response.css('.specs tr, .characteristics tr, .product-params tr'):
            key = row.css('th::text, td.param-name::text').get()
            val = row.css('td::text, td.param-value::text').get()
            if key and val:
                k = key.strip().rstrip(':')
                v = val.strip()
                metadata[k] = v

        # variants: count color or volume options (simple heuristic)
        variants = 0
        color_opts = response.css('.color-variants .option, .property.color .option')
        vol_opts = response.css('.volume-variants .option, .property.volume .option')
        if color_opts:
            variants = max(variants, len(color_opts))
        if vol_opts:
            variants = max(variants, len(vol_opts))

        item = {
            'timestamp': timestamp,
            'RPC': str(rpc),
            'url': url,
            'title': title or '',
            'marketing_tags': marketing,
            'brand': brand or '',
            'section': sections,
            'price_data': price_data,
            'stock': {'in_stock': in_stock, 'count': count},
            'assets': assets,
            'metadata': metadata,
            'variants': variants
        }

        yield item
