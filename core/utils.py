import json
from django.core.serializers.json import DjangoJSONEncoder
import logging
import requests
from bs4 import BeautifulSoup
import random
import time
import re
from django.conf import settings
from serpapi import GoogleSearch

logger = logging.getLogger(__name__)

def format_response(data, message="Success", status=200):
    """
    Standardize API response format.
    """
    return {
        "status": status,
        "message": message,
        "data": data
    }

def search_web(query, num_results=1, rich_results=False):
    """
    Perform a web search using multiple strategies:
    1. SerpAPI (if configured)
    2. Google Custom Search (if configured)
    3. googlesearch-python (Fallback)
    4. DuckDuckGo Lite (Last Resort)
    
    Returns:
        - If rich_results=False: The first valid URL found or a list of URLs if num_results > 1.
        - If rich_results=True: A list of dicts {'title':..., 'link':..., 'snippet':...}
    """
    logger.info(f"Searching web for: {query}")
    results = []

    # --- Strategy 1: SerpAPI (Option 1 from Doc) ---
    serpapi_key = getattr(settings, 'SERPAPI_KEY', None)
    if serpapi_key:
        serpapi_key = serpapi_key.strip().strip('"').strip("'")
    if serpapi_key:
        try:
            logger.info("Using SerpAPI for search...")
            params = {
                "q": query,
                "api_key": serpapi_key,
                "num": num_results,
                "engine": "google"
            }
            search = GoogleSearch(params)
            data = search.get_dict()
            
            if 'organic_results' in data:
                for result in data['organic_results']:
                    link = result.get('link')
                    if link:
                        if rich_results:
                            results.append({
                                'title': result.get('title', ''),
                                'link': link,
                                'snippet': result.get('snippet', ''),
                                'displayLink': result.get('displayed_link', '')
                            })
                        else:
                            results.append(link)
                        if len(results) >= num_results: break
            
            if results:
                logger.info(f"SerpAPI found {len(results)} results")
                return results if (num_results > 1 or rich_results) else results[0]
        except Exception as e:
            logger.error(f"SerpAPI failed: {e}")

    # --- Strategy 2: Google Custom Search API ---
    google_api_key = getattr(settings, 'GOOGLE_API_KEY', None)
    google_cse_id = getattr(settings, 'GOOGLE_CSE_ID', None)
    if google_api_key:
        google_api_key = google_api_key.strip().strip('"').strip("'")
    if google_cse_id:
        match = re.search(r'cx=([A-Za-z0-9:_-]+)', google_cse_id)
        if match:
            google_cse_id = match.group(1)
        google_cse_id = google_cse_id.strip().strip('"').strip("'")
    
    if google_api_key and google_cse_id:
        try:
            logger.info("Using Google Custom Search API...")
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': google_api_key,
                'cx': google_cse_id,
                'q': query,
                'num': num_results
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'items' in data:
                for item in data['items']:
                    link = item.get('link')
                    if link:
                        if rich_results:
                            results.append({
                                'title': item.get('title', ''),
                                'link': link,
                                'snippet': item.get('snippet', ''),
                                'displayLink': item.get('displayLink', '')
                            })
                        else:
                            results.append(link)
                        if len(results) >= num_results: break
            
            if results:
                logger.info(f"Google CSE found {len(results)} results")
                return results if (num_results > 1 or rich_results) else results[0]
        except Exception as e:
            logger.error(f"Google CSE failed: {e}")

    # --- Strategy 3: DuckDuckGo Lite (Fallback) ---
    try:
        from googlesearch import search
        logger.info("Fallback: Using googlesearch-python...")
        # Note: googlesearch-python returns objects if advanced=True
        search_results = search(query, num_results=num_results, advanced=True)
        for result in search_results:
             if result.url:
                 if rich_results:
                     results.append({
                        'title': result.title if hasattr(result, 'title') else result.url,
                        'link': result.url,
                        'snippet': result.description if hasattr(result, 'description') else '',
                        'displayLink': result.url.split('/')[2] if '//' in result.url else result.url
                     })
                 else:
                     results.append(result.url)
                 if len(results) >= num_results: break
        
        if results:
             logger.info(f"googlesearch-python found {len(results)} results")
             return results if (num_results > 1 or rich_results) else results[0]
    except Exception as e:
        logger.warning(f"googlesearch-python failed: {e}")

    # --- Strategy 4: DuckDuckGo Lite (Last Resort) ---
    try:
        logger.info("Last Resort: Using DuckDuckGo Lite...")
        url = "https://lite.duckduckgo.com/lite/"
        data = {
            'q': query
        }
        # Randomize User-Agent to avoid simple blocking
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Origin': 'https://lite.duckduckgo.com',
            'Referer': 'https://lite.duckduckgo.com/'
        }
        
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find result links (DuckDuckGo Lite structure)
        links = soup.find_all('a', class_='result-link')
        
        for link in links:
            href = link.get('href')
            if href and href.startswith('http'):
                # Filter out ads and internal DuckDuckGo links
                if 'duckduckgo.com' in href or 'y.js' in href:
                    continue
                
                if rich_results:
                    title = link.get_text()
                    snippet = ''
                    # Try to find snippet in parent's next sibling or similar
                    # HTML: <tr><td>...link...</td></tr><tr><td>snippet</td></tr>
                    try:
                        # Go up to td, then tr
                        td = link.find_parent('td')
                        if td:
                             tr = td.find_parent('tr')
                             if tr:
                                 snippet_tr = tr.find_next_sibling('tr')
                                 if snippet_tr:
                                     snippet_td = snippet_tr.find('td', class_='result-snippet')
                                     if snippet_td:
                                         snippet = snippet_td.get_text(strip=True)
                    except:
                        pass
                        
                    results.append({
                        'title': title,
                        'link': href,
                        'snippet': snippet,
                        'displayLink': href.split('/')[2] if '//' in href else href
                    })
                else:
                    results.append(href)
                    
                if len(results) >= num_results:
                    break
        
        if results:
            logger.info(f"DuckDuckGo found {len(results)} results")
            return results if (num_results > 1 or rich_results) else results[0]
            
        logger.warning("No search results found.")
        return [] if (num_results > 1 or rich_results) else None
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return [] if rich_results else None
