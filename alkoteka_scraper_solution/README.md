Alkoteka Scrapy parser
======================

Описание
--------
Scrapy-проект для парсинга товаров с alkoteka.com по списку категорий.
Собирает данные в формате JSON, соответствующем заданию.

Запуск
-----
1) Установите зависимости:
   pip install scrapy

2) Поместите список стартовых ссылок в файл start_urls.txt (одна ссылка на строку)
   или отредактируйте переменную START_URLS в spider (spiders/alkoteka_spider.py).

3) (Опционально) Добавьте прокси в файл proxies.txt (одна запись host:port или http://user:pass@host:port).

4) Запустите:
   scrapy crawl alkoteka -O result.json

Примечания по региону
---------------------
Сайт alkoteka может определять регион по cookie или GET-параметру. В spider установлен пример
установки cookie 'region'='Краснодар' и заголовков. Если потребуется другой ключ - отредактируйте
spider или settings.

Структура проекта
-----------------
- alkoteka_scraper/            Scrapy project package
    - spiders/alkoteka_spider.py  основной spider
    - middlewares.py              proxy middleware example
    - items.py                    item definition (if needed)
    - settings.py                 Scrapy settings
- start_urls.txt               файл со списком категорий (пример)
- proxies.txt                  файл со списком прокси (опционально)
- result.json                  результат (при запуске)
