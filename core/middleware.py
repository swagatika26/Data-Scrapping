import logging
from .models import TrafficLog

logger = logging.getLogger(__name__)


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response

        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None

        try:
            TrafficLog.objects.create(
                path=request.path,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as exc:
            logger.warning(f"Traffic logging failed: {exc}")

        return response
