import json
from django.core.serializers.json import DjangoJSONEncoder
import logging
import requests
from bs4 import BeautifulSoup
import random
import time

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

def search_web(query, num_results=1):
    """
    Perform a web search using DuckDuckGo Lite (HTML) to avoid rate limits/API keys.
    Returns the first valid URL found.
    """
    try:
        logger.info(f"Searching web for: {query}")
        url = "https://lite.duckduckgo.com/lite/"
        data = {
            'q': query
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find result links
        results = []
        links = soup.find_all('a', class_='result-link')
        
        for link in links:
            href = link.get('href')
            if href and href.startswith('http'):
                results.append(href)
                if len(results) >= num_results:
                    break
        
        if results:
            logger.info(f"Found URL: {results[0]}")
            return results[0]
            
        logger.warning("No search results found.")
        return None
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return None
