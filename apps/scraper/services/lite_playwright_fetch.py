import time, random
from urllib.parse import urlparse
from contextlib import suppress
from playwright.sync_api import sync_playwright

# Global domain throttle map
last_request_time = {}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]
BLOCK_TOKENS = ["captcha", "cloudflare", "access denied", "verify you are human"]

def _throttle(url: str, min_gap: float = 10.0) -> None:
    host = urlparse(url).netloc.lower()
    now = time.time()
    last = last_request_time.get(host)
    if last:
        wait = (last + min_gap) - now
        if wait > 0:
            time.sleep(wait)
    last_request_time[host] = time.time()

def _is_blocked(html: str) -> bool:
    if not html:
        return True
    text = html.lower()
    return any(tok in text for tok in BLOCK_TOKENS)

def fetch_page(url: str):
    """
    Returns: {"status": "success"|"blocked"|"failed", "html": str|None}
    """
    attempts = 3
    for i in range(attempts):
        try:
            # Domain throttle + human-like delay
            _throttle(url, 10.0)
            time.sleep(random.uniform(3, 8))

            with sync_playwright() as p:
                ua = random.choice(USER_AGENTS)
                browser = p.chromium.launch(headless=True, args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox", "--disable-setuid-sandbox",
                ])
                context = browser.new_context(
                    user_agent=ua,
                    viewport={"width": 1280, "height": 800},
                    locale="en-US",
                )
                page = context.new_page()
                # Light resource blocking for speed/memory
                with suppress(Exception):
                    page.route("**/*", lambda r: r.abort() if r.request.resource_type in ("image","media","font") else r.continue_())

                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                with suppress(Exception):
                    page.wait_for_load_state("networkidle", timeout=10000)
                with suppress(Exception):
                    page.wait_for_timeout(500)
                html = page.content()
                with suppress(Exception): context.close()
                with suppress(Exception): browser.close()

            if _is_blocked(html) or len(html) < 500:
                return {"status": "blocked", "html": None}
            return {"status": "success", "html": html}
        except Exception:
            # Retry after small backoff
            time.sleep(1.5 + i)
            continue
    return {"status": "failed", "html": None}

__all__ = ["fetch_page", "last_request_time"]

