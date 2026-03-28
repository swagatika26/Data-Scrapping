import json
from django.http import JsonResponse, StreamingHttpResponse
from django.conf import settings
from django.utils import timezone
from apps.scraper.services.ollama_service import OllamaService

def deepseek_chat(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    try:
        payload = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON body'}, status=400)
    messages = payload.get('messages')
    prompt = (payload.get('prompt') or '').strip()
    if not messages:
        messages = [{'role': 'user', 'content': prompt}]
    model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-r1:7b')
    host = getattr(settings, 'OLLAMA_HOST', None)
    options = payload.get('options') or {}
    service = OllamaService(host=host, model=model)
    res = service.chat(messages=messages, options=options)
    return JsonResponse({'status': 'success', 'data': res, 'timestamp': timezone.now().isoformat()})

def deepseek_stream(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    try:
        payload = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON body'}, status=400)
    messages = payload.get('messages')
    prompt = (payload.get('prompt') or '').strip()
    if not messages:
        messages = [{'role': 'user', 'content': prompt}]
    model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-r1:7b')
    host = getattr(settings, 'OLLAMA_HOST', None)
    options = payload.get('options') or {}
    service = OllamaService(host=host, model=model)
    def gen():
        for chunk in service.chat_stream(messages=messages, options=options):
            content = ''
            if isinstance(chunk, dict):
                content = (chunk.get('message', {}) or {}).get('content') or chunk.get('response') or ''
            yield content
    return StreamingHttpResponse(gen(), content_type='text/plain; charset=utf-8')
