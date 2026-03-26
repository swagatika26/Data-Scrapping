import random


UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


class RandomUserAgentMiddleware:
    def process_request(self, request, spider):
        request.headers.setdefault(b"User-Agent", random.choice(UA_POOL).encode())
        request.headers.setdefault(b"Accept", b"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        request.headers.setdefault(b"Accept-Language", b"en-US,en;q=0.9")
        request.headers.setdefault(b"DNT", b"1")


class DefaultHeadersMiddleware:
    def process_request(self, request, spider):
        request.headers.setdefault(b"Connection", b"keep-alive")
        request.headers.setdefault(b"Upgrade-Insecure-Requests", b"1")
