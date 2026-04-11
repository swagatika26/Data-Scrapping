import os
import json
import re
import logging
from typing import Optional, List, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

class AIService:
    """
    AI Service with OpenAI as primary and Ollama as fallback.
    Uses OpenAI's gpt-4o-mini model for best performance with scraping tasks.
    Falls back to Ollama local models if OpenAI fails.
    """
    
    _openai_client = None
    _ollama_configured = False

    @classmethod
    def _get_openai_client(cls):
        """Get or initialize OpenAI client"""
        if cls._openai_client is None:
            try:
                from openai import OpenAI, APIError, APIConnectionError
                api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.getenv('OPENAI_API_KEY')
                if not api_key:
                    logger.warning("OPENAI_API_KEY not found in settings or environment")
                    return None
                cls._openai_client = OpenAI(api_key=api_key)
            except ImportError:
                logger.error("OpenAI package not installed. Run: pip install openai")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                return None
        return cls._openai_client

    @classmethod
    def _is_ollama_available(cls) -> bool:
        """Check if Ollama is available and running"""
        try:
            import requests
            ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434') or os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
            response = requests.head(f"{ollama_url}/api/tags", timeout=2)
            return response.status_code in [200, 404]  # 404 is still OK, it means service is up
        except Exception as e:
            if getattr(settings, 'AI_SERVICE_DEBUG', False):
                logger.debug(f"Ollama not available: {e}")
            return False

    @classmethod
    def _call_openai(cls, prompt: str, content: str, max_tokens: int = 4000) -> Optional[str]:
        """
        Call OpenAI API (gpt-4o-mini)
        
        :param prompt: System prompt
        :param content: Content to process
        :param max_tokens: Maximum tokens in response
        :return: Response text or None if failed
        """
        try:
            client = cls._get_openai_client()
            if not client:
                return None

            # Truncate content to stay within token limits
            # GPT-4o-mini has 128k context, but we'll be conservative
            max_chars = 50000
            truncated_content = content[:max_chars]

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": truncated_content}
                ],
                temperature=0.1,  # Lower temperature for consistent JSON output
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None

    @classmethod
    def _call_ollama(cls, prompt: str, content: str) -> Optional[str]:
        """
        Call Ollama API as fallback
        
        :param prompt: System prompt
        :param content: Content to process
        :return: Response text or None if failed
        """
        try:
            import requests
            ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434') or os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
            
            # Truncate content
            max_chars = 20000
            truncated_content = content[:max_chars]
            
            payload = {
                "model": "mistral",  # Default Ollama model, can be customized
                "prompt": f"{prompt}\n\n{truncated_content}",
                "stream": False,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f"Ollama API returned status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            return None

    @classmethod
    def _clean_json_response(cls, text: str) -> str:
        text = (text or "").strip()
        text = re.sub(r'^```json\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return text.strip()

    @classmethod
    def _response_preview(cls, text: Optional[str], limit: int = 300) -> str:
        if text is None:
            return "None"
        cleaned = re.sub(r'\s+', ' ', str(text)).strip()
        return cleaned[:limit]

    @classmethod
    def _extract_json_payload(cls, text: Optional[str]) -> str:
        cleaned = cls._clean_json_response(text)
        if not cleaned:
            return ""
        fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text or "", flags=re.IGNORECASE)
        if fenced_match:
            candidate = fenced_match.group(1).strip()
            if candidate:
                cleaned = candidate
        for pattern in (r"(\[[\s\S]*\])", r"(\{[\s\S]*\})"):
            match = re.search(pattern, cleaned)
            if match:
                return match.group(1).strip()
        return cleaned

    @classmethod
    def _parse_model_json(cls, response: Optional[str], source: str) -> Optional[List[Dict[str, Any]]]:
        payload = cls._extract_json_payload(response)
        if not payload:
            logger.error(f"{source} returned an empty response")
            return None
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"{source} response parsing failed: {e}")
            logger.error(f"{source} raw response preview: {cls._response_preview(response)}")
            return None
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ('items', 'data', 'results', 'products'):
                value = data.get(key)
                if isinstance(value, list):
                    return value
        logger.error(f"{source} returned JSON but not a list. Type: {type(data).__name__}")
        logger.error(f"{source} raw response preview: {cls._response_preview(response)}")
        return None

    @classmethod
    def extract_structured_data(cls, html_content: str, schema_hint: Optional[str] = None, prompt_override: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Extracts structured data from HTML content using OpenAI (main) or Ollama (fallback).
        
        :param html_content: The HTML string to parse
        :param schema_hint: Optional description of what to extract (e.g. "product list with name, price, rating")
        :param prompt_override: Custom prompt to override default
        :return: List of dictionaries or None if failed
        """
        
        if prompt_override:
            prompt = prompt_override
        else:
            prompt = """You are an expert web scraper AI. Extract structured data from the HTML content.
Requirements:
- Identify repeating items (products, articles, jobs, listings, etc.)
- Extract all relevant fields for each item
- Clean the data (remove currency symbols, trim whitespace, normalize values)
- Return ONLY a valid JSON array of objects, no markdown formatting
- Each item should be an object with consistent fields
- If a field is missing, use empty string, not null"""
            
            if schema_hint:
                prompt += f"\nTarget data: {schema_hint}"

        # Try OpenAI first (main service)
        logger.info("Attempting to extract data using OpenAI...")
        response = cls._call_openai(prompt, html_content)
        
        if response:
            data = cls._parse_model_json(response, "OpenAI")
            if data is not None:
                logger.info("OpenAI extraction successful")
                return data

        # Fallback to Ollama if available
        if cls._is_ollama_available():
            logger.info("OpenAI failed, attempting fallback with Ollama...")
            response = cls._call_ollama(prompt, html_content)
            
            if response:
                data = cls._parse_model_json(response, "Ollama")
                if data is not None:
                    logger.info("Ollama extraction successful")
                    return data
        
        logger.error("Both OpenAI and Ollama extraction failed")
        return None

    @classmethod
    def normalize_items(cls, items: List[Dict[str, Any]], schema_hint: Optional[str] = None, prompt_override: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Normalize and clean a list of scraped items using OpenAI (main) or Ollama (fallback).
        
        :param items: List of dictionaries to normalize
        :param schema_hint: Optional hint about the data structure
        :param prompt_override: Custom prompt to override default
        :return: Normalized list of dictionaries or None if failed
        """
        
        if not items or not isinstance(items, list):
            return None

        if prompt_override:
            prompt = prompt_override
        else:
            prompt = """You are a data cleaning and normalization expert.
Clean and normalize the provided JSON list of scraped items.
Requirements:
- Output ONLY valid JSON (no markdown)
- Each item must be an object
- Remove extra whitespace and HTML tags
- Normalize values (trim, lowercase where appropriate)
- Keep URLs as-is
- Use empty strings for missing fields (never null)
- Remove duplicate entries
- Ensure all items have the same keys"""
            
            if schema_hint:
                prompt += f"\nData context: {schema_hint}"

        # Prepare payload (use max 50 items to avoid token limits)
        payload = json.dumps(items[:50], ensure_ascii=False, indent=2)

        # Try OpenAI first
        logger.info("Attempting to normalize items using OpenAI...")
        response = cls._call_openai(prompt, payload, max_tokens=8000)
        
        if response:
            data = cls._parse_model_json(response, "OpenAI normalization")
            if data is not None:
                logger.info("OpenAI normalization successful")
                return data

        # Fallback to Ollama
        if cls._is_ollama_available():
            logger.info("OpenAI failed, attempting normalization with Ollama...")
            response = cls._call_ollama(prompt, payload)
            
            if response:
                data = cls._parse_model_json(response, "Ollama normalization")
                if data is not None:
                    logger.info("Ollama normalization successful")
                    return data
        
        logger.error("Both OpenAI and Ollama normalization failed")
        return None
