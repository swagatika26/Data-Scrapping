# AI Service Upgrade: OpenAI + Ollama Setup Guide

## ✅ Changes Completed

### 1. **Updated requirements.txt**
- Added `openai==1.30.0` - OpenAI Python client
- Added `ollama==0.1.0` - Ollama client for local models

### 2. **Updated settings.py**
Added new configuration variables:
```python
# AI Service Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
AI_SERVICE_DEBUG = os.getenv('AI_SERVICE_DEBUG', 'False') == 'True'
```

### 3. **Completely Rewrote ai_service.py**
- **Primary:** OpenAI (gpt-4o-mini) - Best for web scraping data extraction
- **Fallback:** Ollama (local models) - Acts as backup if OpenAI fails
- Both methods use the same interface - no changes needed to existing code

---

## 🚀 Setup Instructions

### Step 1: Install Updated Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Step 2: Configure Environment Variables

Create or update your `.env` file in the project root:

```env
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Ollama Configuration (OPTIONAL - for local fallback)
OLLAMA_API_URL=http://localhost:11434

# Debug Mode (OPTIONAL)
AI_SERVICE_DEBUG=False
```

### Step 3: Get Your OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Go to API Keys section
4. Create a new API key
5. Copy and paste it in your `.env` file

**Cost Estimate:**
- gpt-4o-mini is very affordable (~$0.15 per 1M input tokens)
- Perfect for web scraping data extraction

### Step 4 (Optional): Setup Ollama as Fallback

If you want local fallback capability:

1. **Install Ollama:**
   - Windows: Download from [ollama.ai](https://ollama.ai)
   - Or via terminal: `brew install ollama` (macOS)

2. **Pull a model:**
   ```bash
   ollama pull mistral
   ```

3. **Start Ollama service:**
   ```bash
   ollama serve
   ```

4. **Update environment:**
   ```env
   OLLAMA_API_URL=http://localhost:11434
   ```

---

## 📊 How It Works

### Extraction Flow:
```
User Request
    ↓
Try OpenAI (gpt-4o-mini)
    ↓
[Success] → Return JSON data
    ↓
[Failure] → Try Ollama (if available)
    ↓
[Success] → Return JSON data
    ↓
[Failure] → Log error and return None
```

### Key Features:
✅ **OpenAI (Main):**
- Model: gpt-4o-mini (optimized for cost + quality)
- Max input: 50,000 characters
- Temperature: 0.1 (consistent JSON output)
- Available: Any time (cloud-based)

✅ **Ollama (Fallback):**
- Model: Mistral (open-source)
- Max input: 20,000 characters
- Temperature: 0.1 (consistent JSON output)
- Available: When running locally

---

## 🔍 Testing Your Setup

### Test 1: OpenAI Connection
```python
from apps.scraper.services.ai_service import AIService

# Simple test
html = "<div class='product'><h2>Product 1</h2><p>$99</p></div>"
result = AIService.extract_structured_data(html)
print(result)
```

### Test 2: Verify Fallback Ready
```python
# Check Ollama availability
from apps.scraper.services.ai_service import AIService
is_available = AIService._is_ollama_available()
print(f"Ollama available: {is_available}")
```

---

## 📝 Environment Checklist

Before running:
- [ ] Installed new requirements: `pip install -r requirements.txt`
- [ ] Created `.env` file with OPENAI_API_KEY
- [ ] Added OPENAI_API_KEY to your environment
- [ ] (Optional) Installed and started Ollama for fallback
- [ ] Tested the connection with code snippet above

---

## 🐛 Troubleshooting

### "OPENAI_API_KEY not found"
- Check `.env` file exists in project root
- Run: `echo $OPENAI_API_KEY` to verify environment variable
- Restart your IDE/terminal after adding to `.env`

### "OpenAI API call failed"
- Verify API key is correct
- Check internet connection
- Review OpenAI account status and billing
- Check API rate limits

### "Ollama API call failed"
- Make sure Ollama service is running: `ollama serve`
- Check OLLAMA_API_URL is correct (default: http://localhost:11434)
- Pull required model: `ollama pull mistral`

### Enable Debug Mode
Add to `.env`:
```env
AI_SERVICE_DEBUG=True
```
This will log additional details about fallback attempts.

---

## 📈 Migration Notes

- **No code changes needed** for existing scraper code
- Existing calls to `AIService.extract_structured_data()` and `AIService.normalize_items()` work as before
- Better performance due to gpt-4o-mini optimizations for structured data
- More reliable with automatic fallback to Ollama

---

## 💡 Recommendations

1. **Start with OpenAI only** - More reliable for production
2. **Keep Ollama config handy** - Great for development/testing
3. **Monitor API usage** - OpenAI dashboard shows real-time stats
4. **Use schema hints** - Improves extraction quality:
   ```python
   AIService.extract_structured_data(
       html,
       schema_hint="e-commerce products with name, price, rating, in-stock status"
   )
   ```

---

## 🔗 Useful Links

- OpenAI API Docs: https://platform.openai.com/docs/api-reference
- Ollama GitHub: https://github.com/ollama/ollama
- gpt-4o-mini Pricing: https://platform.openai.com/pricing
- Models Comparison: https://platform.openai.com/docs/models

---

**Questions or Issues?** Check the logs in Django debug mode or enable AI_SERVICE_DEBUG=True
