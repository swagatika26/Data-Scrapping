import logging
import requests
from bs4 import BeautifulSoup
import re
import random
import time
import json
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class ScraperService:
    """
    Service layer for handling scraping logic with enhanced support for JS-heavy sites via structured data.
    """
    
    def try_playwright(self, url, timeout_ms=90000):
        """Attempt to scrape using Playwright to bypass 403/CAPTCHA."""
        try:
            # Import here to avoid hard dependency at module level
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                logger.info("Launching Playwright for fallback scrape...")
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled", 
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-infobars",
                        "--window-position=0,0",
                        "--ignore-certificate-errors",
                        "--ignore-certificate-errors-spki-list",
                        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                    ]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                    timezone_id="America/New_York",
                    geolocation={"latitude": 40.7128, "longitude": -74.0060},
                    permissions=["geolocation"]
                )
                
                # Stealth injection
                stealth_js = """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                window.chrome = { runtime: {} };
                """
                
                page = context.new_page()
                page.add_init_script(stealth_js)
                
                try:
                    logger.info(f"Playwright navigating to {url}")
                    page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                    page.wait_for_timeout(5000) # Wait for dynamic content/checks
                    
                    # Scroll down to trigger lazy loading
                    for _ in range(5):
                        page.mouse.wheel(0, 500)
                        page.wait_for_timeout(500)
                    
                    # Wait for loading screens to disappear
                    try:
                        # Common loading text indicators
                        loading_indicators = [
                            "text=Just a moment", 
                            "text=finding great stays", 
                            "text=loading", 
                            "text=please wait"
                        ]
                        for indicator in loading_indicators:
                            try:
                                # Wait up to 5s for indicator to vanish if present
                                if page.is_visible(indicator, timeout=1000):
                                    logger.info(f"Waiting for '{indicator}' to disappear...")
                                    page.wait_for_selector(indicator, state='hidden', timeout=10000)
                            except:
                                pass # Indicator not found or didn't disappear, proceed anyway
                    except Exception as e:
                        logger.warning(f"Error waiting for loading screen: {e}")

                    content = page.content()
                    title = page.title()
                    logger.info(f"Playwright success. Title: {title}, Content len: {len(content)}")
                    
                    browser.close()
                    return content
                except Exception as e:
                    browser.close()
                    logger.error(f"Playwright navigation failed: {e}")
                    return None
        except Exception as e:
            logger.error(f"Playwright setup failed: {e}")
            return None
    
    def execute_scrape(self, url, options=None):
        """
        Execute the scraping logic with robust fallback strategies.
        """
        logger.info(f"Starting scrape for {url}")
        
        # Check if input is a URL
        if not url.startswith('http'):
            return {
                "url": url,
                "title": "Invalid URL",
                "products": [],
                "count": 0,
                "error": "Please provide a valid URL starting with http:// or https://"
            }
        
        try:
            html_content = None
            options = options or {}
            req_timeout = int(options.get('timeout', 30))
            retry_limit = max(1, int(options.get('retry_limit', 3)))
            
            # 1. Try Requests first
            try:
                # Use improved headers to mimic a real browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'max-age=0',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Connection': 'keep-alive',
                }
                
                attempt = 0
                last_exc = None
                while attempt < retry_limit and not html_content:
                    time.sleep(random.uniform(0.8, 1.6))
                    session = requests.Session()
                    try:
                        response = session.get(url, headers=headers, timeout=req_timeout)
                        if response.status_code == 403 or "captcha" in response.url.lower() or (len(response.content) < 5000 and "captcha" in response.text.lower()):
                            logger.warning(f"Requests blocked (Status: {response.status_code}), switching to Playwright...")
                            break
                        response.raise_for_status()
                        html_content = response.content
                    except Exception as e:
                        last_exc = e
                        attempt += 1
                if not html_content and last_exc:
                    logger.warning(f"Requests failed after {retry_limit} attempts: {last_exc}, switching to Playwright...")
                    html_content = self.try_playwright(url, timeout_ms=req_timeout * 1000)
            except Exception as e:
                logger.warning(f"Requests failed: {e}, switching to Playwright...")
                html_content = self.try_playwright(url, timeout_ms=req_timeout * 1000)
            
            if not html_content:
                raise Exception("Failed to retrieve content via both Requests and Playwright.")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check for DataDome/CAPTCHA
            if soup.find('iframe', src=re.compile(r'captcha-delivery\.com')) or \
               "datadome" in str(soup).lower() or \
               (soup.title and soup.title.get_text() and "captcha" in soup.title.get_text().lower()):
                raise Exception("Access Denied: Protected by DataDome/CAPTCHA. Please try a different URL or use a proxy service.")

            parsed_url = urlparse(url)
            if "linkedin.com" in parsed_url.netloc:
                page_text = soup.get_text(" ", strip=True).lower()
                title_text = soup.title.get_text(strip=True).lower() if soup.title else ""
                if any(token in page_text for token in ["sign in", "sign up", "join linkedin", "user agreement", "cookie policy"]) or any(token in title_text for token in ["sign in", "linkedin login"]):
                    return {
                        "url": url,
                        "title": "LinkedIn Login Wall",
                        "products": [],
                        "count": 0,
                        "error": "LinkedIn restricts automated scraping. The page returned a login wall, so no usable data can be extracted."
                    }
                return {
                    "url": url,
                    "title": "LinkedIn Restricted",
                    "products": [],
                    "count": 0,
                    "error": "LinkedIn restricts automated scraping. Please use an approved API or a public export for reliable data."
                }

            products = []
            seen_urls = set()
            rank = 1

            # Helper to clean text
            def clean_text(text):
                if not text: return ""
                return " ".join(text.split())

            # Helper to find price
            def find_price(element):
                if not element: return "N/A"
                text = element.get_text(" ", strip=True)
                # 1. Look for currency symbols
                price_match = re.search(r'[\$€£₹]\s*[\d,]+(?:\.\d{2})?', text)
                if price_match: return price_match.group(0)
                
                # 2. Look for "Rs." or "INR"
                rs_match = re.search(r'(?:Rs\.?|INR|USD|EUR)\s*[\d,]+(?:\.\d{2})?', text, re.IGNORECASE)
                if rs_match: return rs_match.group(0)
                
                return "N/A"

            # Helper to find rating
            def find_rating(element):
                if not element: return ""
                
                # 1. Check aria-label (common for stars)
                try:
                    for child in element.find_all(True, recursive=True):
                        if child.has_attr('aria-label'):
                            label = child['aria-label']
                            if re.search(r'\d(\.\d)?\s*out of\s*5', label, re.IGNORECASE):
                                return label
                            if re.search(r'\d(\.\d)?\s*stars', label, re.IGNORECASE):
                                return label
                except: pass

                # 2. Check text patterns like "4.5" or "4.5/5"
                text = element.get_text(" ", strip=True)
                rating_match = re.search(r'\b[1-5](\.\d)?\s*/\s*5', text)
                if rating_match: return rating_match.group(0)
                
                # 3. Look for specific classes
                rating_el = element.select_one('[class*="rating"], [class*="stars"], [class*="score"], [class*="review-score"]')
                if rating_el:
                    val = rating_el.get_text(strip=True)
                    # Match 4.5 or 4
                    if re.match(r'^[1-5](\.\d)?$', val):
                        return val
                
                return ""

            # Helper to find reviews
            def find_reviews(element):
                if not element: return ""
                text = element.get_text(" ", strip=True)
                
                # Pattern: digits reviews/ratings
                rev_match = re.search(r'([\d,]+)\s*(?:reviews|ratings)', text, re.IGNORECASE)
                if rev_match:
                    return rev_match.group(1)

                # Pattern: (digits) - strictly digits and commas
                paren_match = re.search(r'\(([\d,]+)\)', text)
                if paren_match:
                    # Verify it's not a price (no currency inside)
                    if not re.search(r'[\$€£₹]', paren_match.group(0)):
                        return paren_match.group(1)
                    
                return ""
            
            # Helper to find image
            def find_image(element):
                if not element: return ""
                img = element.find('img', src=True)
                if img:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if src and not src.startswith('data:'):
                        return src
                # Check for background image in style
                style = element.get('style', '')
                bg_match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                if bg_match:
                    return bg_match.group(1)
                return ""

            # Helper to find phone
            def find_phone(element):
                if not element: return ""
                # 1. Check for tel: links
                tel_link = element.find('a', href=re.compile(r'^tel:'))
                if tel_link:
                    return tel_link['href'].replace('tel:', '').strip()
                
                text = element.get_text(" ", strip=True)
                # 2. Regex for phone numbers
                # Matches: +1-555-555-5555, (555) 555-5555, 555 555 5555
                phone_match = re.search(r'(?:(?:\+|00)\d{1,3}[-\s.]?)?(?:\(?\d{3}\)?[-\s.]?)?\d{3}[-\s.]?\d{4}', text)
                if phone_match:
                    # Filter out simple dates or years like 2023-2024 if they match
                    val = phone_match.group(0)
                    if len(re.sub(r'\D', '', val)) < 7: return "" 
                    return val
                return ""

            # Helper to find email
            def find_email(element):
                if not element: return ""
                # 1. Check for mailto: links
                mail_link = element.find('a', href=re.compile(r'^mailto:'))
                if mail_link:
                    return mail_link['href'].replace('mailto:', '').split('?')[0].strip()
                
                text = element.get_text(" ", strip=True)
                # 2. Regex for email
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                if email_match:
                    return email_match.group(0)
                return ""

            # Strategy 0: Next.js / JSON Data Blob Extraction (New)
            # Many modern React sites store state in a JSON script tag
            json_scripts = soup.find_all('script', type='application/json')
            for script in json_scripts:
                try:
                    if not script.string: continue
                    # Check for Next.js data
                    if script.get('id') == '__NEXT_DATA__' or 'props' in script.string[:100]:
                        data = json.loads(script.string)
                        
                        # Recursive search for objects with 'name', 'title', 'price', etc.
                        def extract_items_from_json(obj, depth=0):
                            items = []
                            if depth > 5: return items
                            
                            if isinstance(obj, dict):
                                # Check if this dict looks like a product/item
                                if ('name' in obj or 'title' in obj) and ('id' in obj or 'slug' in obj or 'url' in obj):
                                    name = obj.get('name') or obj.get('title')
                                    if name and isinstance(name, str) and len(name) > 3:
                                        items.append({
                                            'name': name,
                                            'price': obj.get('price', obj.get('amount', '')),
                                            'url': obj.get('url', obj.get('slug', '')),
                                            'image': obj.get('image', obj.get('thumbnail', '')),
                                            'rating': obj.get('rating', obj.get('stars', '')),
                                            'reviews': obj.get('reviewCount', obj.get('reviews', '')),
                                            'phone': obj.get('telephone', obj.get('phone', '')),
                                            'email': obj.get('email', '')
                                        })
                                
                                for k, v in obj.items():
                                    if isinstance(v, (dict, list)):
                                        items.extend(extract_items_from_json(v, depth+1))
                                        
                            elif isinstance(obj, list):
                                for item in obj:
                                    items.extend(extract_items_from_json(item, depth+1))
                                    
                            return items

                        extracted = extract_items_from_json(data)
                        # Filter duplicates and valid items
                        for item in extracted:
                            if not item['name']: continue
                            item_name = item['name']
                            if item_name in [p['name'] for p in products]: continue
                            
                            products.append({
                                'rank': rank,
                                'name': item_name,
                                'price': str(item.get('price', '')),
                                'rating': str(item.get('rating', '')),
                                'reviews': str(item.get('reviews', '')),
                                'phone': str(item.get('phone', '')),
                                'email': str(item.get('email', '')),
                                'id': f"NEXT-{rank:04d}",
                                'status': "App Data",
                                'url': str(item.get('url', url))
                            })
                            rank += 1
                            if rank > 50: break
                except:
                    continue

            # Strategy 1: Extract JSON-LD (Structured Data)
            # This is highly effective for e-commerce (Product, ItemList) and Travel (Hotel, Flight)
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    if not script.string: continue
                    data = json.loads(script.string)
                    
                    # Normalize to list if single object
                    if isinstance(data, dict):
                        data_list = [data]
                    else:
                        data_list = data
                        
                    for item in data_list:
                        # Handle Graph structure
                        if '@graph' in item:
                            items_to_check = item['@graph']
                        else:
                            items_to_check = [item]
                            
                        for entity in items_to_check:
                            entity_type = entity.get('@type', '')
                            if isinstance(entity_type, list):
                                entity_type = entity_type[0] if entity_type else ''
                                
                            # Check for Product, Hotel, or generic Item
                            if entity_type in ['Product', 'Hotel', 'LodgingBusiness', 'Course', 'Event', 'Recipe']:
                                name = entity.get('name', '')
                                if not name: continue
                                
                                # Try to find price
                                price = "N/A"
                                offers = entity.get('offers')
                                if offers:
                                    if isinstance(offers, list):
                                        offers = offers[0]
                                    if isinstance(offers, dict):
                                        price_val = offers.get('price')
                                        currency = offers.get('priceCurrency', '')
                                        if price_val:
                                            price = f"{currency} {price_val}".strip()
                                
                                # Try to find rating
                                rating = ""
                                agg_rating = entity.get('aggregateRating')
                                if agg_rating and isinstance(agg_rating, dict):
                                    rating_val = agg_rating.get('ratingValue')
                                    if rating_val:
                                        rating = f"{rating_val}/5"

                                # Try to find reviews
                                reviews = ""
                                if agg_rating and isinstance(agg_rating, dict):
                                    review_count = agg_rating.get('reviewCount')
                                    if review_count:
                                        reviews = f"{review_count} reviews"
                                
                                # Try to find image
                                image = entity.get('image', '')
                                if isinstance(image, list): image = image[0]
                                if isinstance(image, dict): image = image.get('url', '')
                                
                                # Try to find phone and email
                                phone = entity.get('telephone', '')
                                if isinstance(phone, list): phone = phone[0]
                                email = entity.get('email', '')
                                if isinstance(email, list): email = email[0]

                                # Try to find URL
                                item_url = entity.get('url', '')
                                if not item_url: item_url = url # Fallback to page URL if single item
                                else: item_url = urljoin(url, item_url)

                                if item_url in seen_urls: continue
                                seen_urls.add(item_url)
                                
                                products.append({
                                    'rank': rank,
                                    'name': name,
                                    'price': price if price != "N/A" else "",
                                    'rating': rating,
                                    'reviews': reviews,
                                    'phone': phone,
                                    'email': email,
                                    'id': f"JSON-{rank:04d}",
                                    'status': "Structured Data",
                                    'url': item_url
                                })
                                rank += 1
                                
                            # Check for ItemList (Category pages)
                            elif entity_type == 'ItemList':
                                list_items = entity.get('itemListElement', [])
                                for list_item in list_items:
                                    item_data = list_item.get('item', {})
                                    if not item_data: continue
                                    
                                    # Handle string URL items
                                    if isinstance(item_data, str):
                                        item_url = item_data
                                        name = "Item " + str(list_item.get('position', rank))
                                        phone = ""
                                        email = ""
                                    else:
                                        name = item_data.get('name', '')
                                        item_url = item_data.get('url', '')
                                        phone = item_data.get('telephone', '')
                                        email = item_data.get('email', '')
                                    
                                    if not name: continue
                                    
                                    if item_url:
                                        item_url = urljoin(url, item_url)
                                        if item_url in seen_urls: continue
                                        seen_urls.add(item_url)
                                    
                                    products.append({
                                        'rank': rank,
                                        'name': name,
                                        'price': "",
                                        'phone': phone,
                                        'email': email,
                                        'id': f"LIST-{rank:04d}",
                                        'status': "Structured Data",
                                        'url': item_url or url
                                    })
                                    rank += 1
                except Exception as e:
                    logger.warning(f"Failed to parse JSON-LD: {e}")
                    continue

            # Check quality of existing products (from JSON-LD/Next.js)
            valid_prices = sum(1 for p in products if p.get('price') and p.get('price') != "N/A")
            quality_score = valid_prices / len(products) if products else 0
            
            # Strategy 2: AI-Enhanced Structure Clustering (Replaces old Pattern-Based)
            # This logic mimics visual AI by grouping elements based on structural similarity (DOM fingerprinting)
            # rather than just class names, ensuring higher accuracy.
            # TRIGGER: Run if we have few items OR if the existing items have poor data (missing prices)
            if len(products) < 5 or quality_score < 0.5:
                logger.info(f"Triggering AI Clustering. Existing items: {len(products)}, Quality: {quality_score:.2f}")
                
                # --- NEW: Try Gemini AI First ---
                try:
                    from apps.scraper.services.ai_service import AIService
                    # Pass the raw HTML (soup object converted to string)
                    ai_products = AIService.extract_structured_data(str(soup), schema_hint="products or items with name, price, image, link, date")
                    
                    if ai_products and isinstance(ai_products, list) and len(ai_products) > 0:
                        logger.info(f"Gemini AI extracted {len(ai_products)} items.")
                        
                        # Add valid AI items to our products list
                        for p in ai_products:
                            # Normalize keys
                            if not isinstance(p, dict): continue
                            
                            item = {
                                'name': p.get('name') or p.get('title') or p.get('product_name') or 'Unknown Item',
                                'price': p.get('price') or p.get('cost') or 'N/A',
                                'image': p.get('image') or p.get('img') or p.get('image_url') or '',
                                'link': p.get('link') or p.get('url') or p.get('href') or '',
                                'date': p.get('date') or p.get('published_at') or p.get('time') or '',
                                'rating': p.get('rating') or 'N/A',
                                'reviews': p.get('reviews') or '0',
                                'id': f"AI-{len(products)+1:04d}",
                                'status': "AI Extracted"
                            }
                            
                            # Ensure absolute URLs for links and images
                            if item['link'] and not item['link'].startswith(('http', '//')):
                                item['link'] = urljoin(url, item['link'])
                            if item['image'] and not item['image'].startswith(('http', '//')):
                                item['image'] = urljoin(url, item['image'])
                                
                            products.append(item)
                            
                        # If AI succeeded significantly, we can return early or skip heuristics
                        if len(products) > 5:
                            logger.info("AI extraction successful, skipping heuristic clustering.")
                            return products
                except Exception as ai_e:
                    logger.error(f"AI Service integration error: {ai_e}")
                # -------------------------------

                # 1. Identify "Repeated Structures" - The hallmark of a list/grid
                candidates = []
                # Scan common containers
                for tag in ['div', 'article', 'li', 'tr']:
                    elements = soup.find_all(tag)
                    for el in elements:
                        # Skip tiny elements
                        if len(el.get_text(strip=True)) < 10: continue
                        
                        # Generate a "Structure Fingerprint"
                        # E.g. "div>a+span+div"
                        fingerprint = []
                        for child in el.children:
                            if child.name:
                                fingerprint.append(child.name)
                                # Add class-based hint if significant
                                if child.get('class'):
                                    fingerprint.append(f".{sorted(child.get('class'))[0]}") 
                        
                        fp_str = ">".join(fingerprint)
                        if len(fingerprint) >= 2: # Must have some complexity
                            candidates.append({
                                'el': el,
                                'fp': fp_str,
                                'text_len': len(el.get_text(strip=True))
                            })

                # 2. Cluster by Fingerprint
                clusters = {}
                for c in candidates:
                    fp = c['fp']
                    if fp not in clusters: clusters[fp] = []
                    clusters[fp].append(c['el'])

                # 3. Select Best Cluster (Heuristic: Count > 3, High Text Content)
                best_cluster = []
                max_score = 0
                
                for fp, items in clusters.items():
                    if len(items) < 3: continue # Too few to be a list
                    if len(items) > 200: continue # Too many, likely noise/grid cells
                    
                    # Score = Count * Avg Text Length
                    avg_len = sum(len(i.get_text(strip=True)) for i in items) / len(items)
                    
                    # Boost score if items contain price patterns (HUGE BOOST for E-commerce)
                    has_price_count = sum(1 for i in items if re.search(r'[\$€£₹]|Rs\.?|INR|USD|EUR', i.get_text()))
                    price_density = has_price_count / len(items)
                    
                    price_boost = 1.0
                    if price_density > 0.3:
                        price_boost = 10.0  # Massive boost if consistent prices found
                    elif price_density > 0.0:
                        price_boost = 2.0
                    
                    # Boost if items have images
                    has_image_count = sum(1 for i in items if i.find('img'))
                    image_density = has_image_count / len(items)
                    image_boost = 2.0 if image_density > 0.5 else 1.0

                    # Penalize short text items (likely category buttons)
                    if avg_len < 30 and price_density < 0.1:
                        price_boost = 0.01
                    
                    # Penalize massive items (likely whole sections)
                    if avg_len > 1000:
                         price_boost = 0.1

                    score = len(items) * (min(avg_len, 500)) * price_boost * image_boost
                    
                    if score > max_score:
                        max_score = score
                        best_cluster = items
                
                # Fallback: If no good cluster found, try to find ANY cluster with prices
                if max_score < 1000 and not best_cluster:
                    for fp, items in clusters.items():
                         has_price_count = sum(1 for i in items if re.search(r'[\$€£₹]|Rs\.?|INR|USD|EUR', i.get_text()))
                         if has_price_count >= 3:
                             best_cluster = items
                             break

                # 4. Extract Data from Best Cluster
                for card in best_cluster:
                    # Find Link (Priority: deepest a, or first a)
                    links = card.find_all('a', href=True)
                    if not links: continue
                    
                    # Heuristic: The title link usually has the most text or is a header
                    best_link = max(links, key=lambda l: len(l.get_text(strip=True)))
                    href = urljoin(url, best_link['href'])
                    
                    # NOTE: We do NOT skip seen_urls here, because we might want to UPGRADE them with better data (Merge)
                    
                    # Find Name
                    name = clean_text(best_link.get_text())
                    if not name or len(name) < 3:
                         # Try finding a header inside the card
                         header = card.find(['h1', 'h2', 'h3', 'h4', 'span'])
                         if header: name = clean_text(header.get_text())
                    
                    if not name: continue

                    # Smart Filtering (AI-Simulated)
                    lower_name = name.lower()
                    if len(lower_name) < 4: continue # Too short
                    if any(x == lower_name for x in ['home', 'menu', 'search', 'login', 'sign up', 'about', 'contact', 'terms', 'privacy', 'read more', 'view details', 'add to cart']):
                        continue
                    if any(x in lower_name for x in ['privacy policy', 'terms of use', 'all rights reserved', 'skip to', 'loading...']):
                        continue
                    
                    # New: Filter out Category-like items (e.g. "Under 10k", "Shop by Brand")
                    if re.search(r'^(shop by|browse|view all|under \d+|up to \d+|more like this|customer care|download app)', lower_name):
                        continue

                    # Find Price (Heuristic: Look for currency symbols in the card)
                    price = find_price(card)
                    rating = find_rating(card)
                    reviews = find_reviews(card)
                    image = find_image(card)
                    phone = find_phone(card)
                    email = find_email(card)
                    
                    # New: If generic name and NO price, skip it (it's likely a category tile)
                    if not price and (len(name.split()) < 3 or "shop" in lower_name or "category" in lower_name):
                        continue
                    
                    # New: Mandatory Price OR Rating OR Image check for generic clusters
                    if not price and not rating and not image and not phone and not email and len(name) < 30:
                        continue

                    # Smart Merge: If URL exists but lacks data, update it!
                    if href in seen_urls:
                        existing_p = next((p for p in products if p.get('url') == href), None)
                        if existing_p:
                            # Upgrade if we have better data
                            if not existing_p.get('price') and price:
                                 existing_p['price'] = price
                                 existing_p['status'] += " + AI"
                            if not existing_p.get('rating') and rating:
                                 existing_p['rating'] = rating
                            if not existing_p.get('reviews') and reviews:
                                 existing_p['reviews'] = reviews
                            if not existing_p.get('image') and image:
                                 existing_p['image'] = image
                            if not existing_p.get('phone') and phone:
                                 existing_p['phone'] = phone
                            if not existing_p.get('email') and email:
                                 existing_p['email'] = email
                        continue
                    
                    seen_urls.add(href)
                    products.append({
                        'rank': rank,
                        'name': name,
                        'price': price if price != "N/A" else "",
                        'rating': rating,
                        'reviews': reviews,
                        'image': image,
                        'phone': phone,
                        'email': email,
                        'id': f"AI-CLUS-{rank:04d}", # Mark as AI-Clustered
                        'status': "AI Extracted",
                        'url': href
                    })
                    rank += 1
                    if rank > 100: break

            # Strategy 3: Specific Class Selectors (Fallback)
            if len(products) < 5:
                candidates = []
                for class_name in ['product', 'item', 'card', 'listing', 'result', 'grid-item', 'shop-item', 'offer', 'deal', 'hotel', 'flight']:
                    candidates.extend(soup.select(f'[class*="{class_name}"]'))
                    candidates.extend(soup.select(f'[id*="{class_name}"]'))
                
                candidates = list(set(candidates))
                for card in candidates:
                     # (Logic reused from above, simplified here for brevity as Pattern Match usually catches this)
                     link = card.find('a', href=True)
                     if not link: continue
                     href = urljoin(url, link['href'])
                     if href in seen_urls: continue
                     name = clean_text(card.get_text())[:100]
                     if len(name) > 3:
                        seen_urls.add(href)
                        products.append({
                            'rank': rank,
                            'name': name,
                            'price': find_price(card),
                            'rating': find_rating(card),
                            'reviews': find_reviews(card),
                            'image': find_image(card),
                            'phone': find_phone(card),
                            'email': find_email(card),
                            'id': f"CSS-{rank:04d}",
                            'status': "Found",
                            'url': href
                        })
                        rank += 1
                    
            # Strategy 4: Open Graph / Meta Data (If a single page is scraped)
            if not products:
                og_title = soup.find("meta", property="og:title")
                og_price = soup.find("meta", property="product:price:amount")
                og_currency = soup.find("meta", property="product:price:currency")
                
                if og_title:
                    name = og_title.get("content", "")
                    price = ""
                    if og_price:
                        price = og_price.get("content", "")
                        if og_currency:
                            price = f"{og_currency.get('content')} {price}"
                    
                    products.append({
                        'rank': 1,
                        'name': name,
                        'price': price,
                        'id': "OG-DATA",
                        'status': "Meta Data",
                        'url': url
                    })

            # Strategy 4: Fallback Link Scraping (Last Resort)
            if len(products) < 3:
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    href = urljoin(url, href)
                    
                    if href in seen_urls: continue
                    
                    name = clean_text(link.get_text())
                    if not name or len(name) < 10 or len(name) > 100: continue
                        
                    # Refined filtering
                    lower_name = name.lower()
                    if lower_name in ['home', 'menu', 'search', 'login', 'sign up', 'about', 'contact', 'terms', 'privacy']:
                        continue
                    
                    if any(x in lower_name for x in ['privacy policy', 'terms of use', 'skip to', 'all rights reserved']):
                        continue
                        
                    price = find_price(link.parent)
                    rating = find_rating(link.parent)
                    reviews = find_reviews(link.parent)
                    image = find_image(link.parent)
                    phone = find_phone(link.parent)
                    email = find_email(link.parent)
                    
                    seen_urls.add(href)
                    products.append({
                        'rank': rank,
                        'name': name,
                        'price': price if price != "N/A" else "",
                        'rating': rating,
                        'reviews': reviews,
                        'image': image,
                        'phone': phone,
                        'email': email,
                        'id': f"LNK-{rank:04d}",
                        'status': "Found",
                        'url': href
                    })
                    rank += 1
                    if rank > 50: break
            
            # Strategy 5: Table Scraping (New)
            if len(products) < 5:
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) < 2: continue
                    
                    # Assume first row is header or check if it has th
                    headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
                    
                    for row in rows[1:]: # Skip header
                        cols = row.find_all('td')
                        if not cols: continue
                        
                        # Try to find name and price in columns
                        row_text = [col.get_text(strip=True) for col in cols]
                        if not row_text: continue
                        
                        # Heuristic: Name is usually the first non-numeric long column
                        name = ""
                        price = ""
                        rating = ""
                        reviews = ""
                        phone = ""
                        email = ""
                        url_found = ""
                        
                        for i, text in enumerate(row_text):
                            if not name and len(text) > 3 and not re.match(r'^[\d\.,]+$', text):
                                name = text
                                # Check for link in this column
                                link = cols[i].find('a', href=True)
                                if link:
                                    url_found = urljoin(url, link['href'])
                            elif not price and re.search(r'[\$€£₹]', text):
                                price = text
                            elif not rating and (re.search(r'\d(\.\d)?\s*/\s*5', text) or 'star' in text.lower()):
                                rating = text
                            elif not reviews and re.search(r'\d+\s*(?:reviews|ratings)', text, re.IGNORECASE):
                                reviews = text
                            
                            # Phone and Email check
                            p_check = find_phone(cols[i])
                            if p_check: phone = p_check
                            
                            e_check = find_email(cols[i])
                            if e_check: email = e_check
                        
                        if name:
                            if not url_found:
                                # Look for any link in the row
                                link = row.find('a', href=True)
                                if link: url_found = urljoin(url, link['href'])
                            
                            products.append({
                                'rank': rank,
                                'name': name,
                                'price': price,
                                'rating': rating,
                                'reviews': reviews,
                                'phone': phone,
                                'email': email,
                                'id': f"TBL-{rank:04d}",
                                'status': "Table Data",
                                'url': url_found or url
                            })
                            rank += 1
                            if rank > 50: break

            # Strategy 6: Generic Content Extraction (Last Resort)
            if not products:
                # Check for blocking messages first
                page_text = soup.get_text().lower()
                if "captcha" in page_text or "access denied" in page_text or "cloudflare" in page_text:
                     return {
                        "url": url,
                        "title": "Access Denied / Captcha",
                        "products": [],
                        "count": 0,
                        "error": "Scraping blocked by security check (Captcha/Cloudflare)"
                    }

                # Find paragraphs/divs with significant text
                content_blocks = []
                content_blocks.extend(soup.find_all('p'))
                content_blocks.extend(soup.find_all('div'))
                content_blocks.extend(soup.find_all('article'))
                
                for block in content_blocks:
                    # Skip if it contains many links (nav/footer)
                    if len(block.find_all('a')) > 3: continue
                    
                    text = clean_text(block.get_text())
                    if len(text) > 50 and len(text) < 2000: # Relaxed length limits
                        # Check uniqueness
                        if any(text[:30] in p['name'] for p in products): continue
                        
                        products.append({
                            'rank': rank,
                            'name': text[:150] + "..." if len(text) > 150 else text,
                            'price': find_price(block),
                            'rating': find_rating(block),
                            'reviews': find_reviews(block),
                            'phone': find_phone(block),
                            'email': find_email(block),
                            'id': f"TXT-{rank:04d}",
                            'status': "Content",
                            'url': url
                        })
                        rank += 1
                        if rank > 20: break

            # Final Fallback: Page Info - REMOVED COMPLETELY
            # We want to return 0 items if no real data is found, so the API can report a proper failure.
            # Adding a "Page Title" item just masks the failure and frustrates the user.
            
            return {
                "url": url,
                "title": soup.title.get_text(strip=True) if soup.title else "Scraped Page",
                "products": products,
                "count": len(products)
            }
            
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {str(e)}")
            return {
                "url": url,
                "title": "Error Scraping Page",
                "products": [],
                "count": 0,
                "error": str(e)
            }

    def validate_url(self, url):
        """
        Validate if the URL is scrapable.
        """
        return url.startswith("http")
