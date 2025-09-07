import random
import os

class ProxyMiddleware:
    """Simple proxy rotation middleware.
    Reads proxies from ../proxies.txt (one per line). If file is empty or not present, does nothing.
    Configure proxies.txt with lines like:
      http://user:pass@host:port
      http://host:port
    """
    def __init__(self):
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        pfile = os.path.join(base, 'proxies.txt')
        self.proxies = []
        try:
            with open(pfile, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    self.proxies.append(line)
        except Exception:
            self.proxies = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        if not self.proxies:
            return
        proxy = random.choice(self.proxies)
        request.meta['proxy'] = proxy
