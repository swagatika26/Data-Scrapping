import os
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

class AIService:
    _configured = False

    @classmethod
    def configure(cls):
        if cls._configured:
            return True
        
        api_key = getattr(settings, 'GOOGLE_API_KEY', None) or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found in settings or environment.")
            return False
        
        try:
            genai.configure(api_key=api_key)
            cls._configured = True
            return True
        except Exception as e:
            logger.error(f"Failed to configure Google Generative AI: {e}")
            return False

    @classmethod
    def extract_structured_data(cls, html_content, schema_hint=None):
        """
        Extracts structured data from HTML content using Gemini.
        
        :param html_content: The HTML string to parse (should be truncated if too large)
        :param schema_hint: Optional description of what to extract (e.g. "product list with name, price, rating")
        :return: List of dictionaries or None if failed
        """
        if not cls.configure():
            return None

        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = """
            You are an expert web scraper. Extract the main data from this HTML snippet into a JSON list of objects.
            Identify the repeating items (like products, articles, jobs, etc.).
            Clean the data (remove currency symbols, extra whitespace).
            Return ONLY the valid JSON list, no markdown formatting.
            """
            
            if schema_hint:
                prompt += f"\nFocus on extracting: {schema_hint}"
                
            # Truncate HTML to avoid token limits (rough estimate)
            # Gemini 1.5 Flash has a large context window, but let's be safe and efficient
            max_chars = 30000 
            truncated_html = html_content[:max_chars]
            
            response = model.generate_content([prompt, truncated_html])
            
            import json
            import re
            
            text = response.text.strip()
            # Remove markdown code blocks if present
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            data = json.loads(text)
            return data
            
        except Exception as e:
            logger.error(f"AI Extraction failed: {e}")
            return None
