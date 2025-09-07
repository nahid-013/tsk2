# Not strictly required for this task, but provided for completeness.
from scrapy import Item, Field

class ProductItem(Item):
    timestamp = Field()
    RPC = Field()
    url = Field()
    title = Field()
    marketing_tags = Field()
    brand = Field()
    section = Field()
    price_data = Field()
    stock = Field()
    assets = Field()
    metadata = Field()
    variants = Field()
