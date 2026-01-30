from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ScraperJob
from .serializers import ScraperJobSerializer
from .services.scraper_service import ScraperService
from apps.tasks.tasks import run_scraper_task

class ScraperJobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing scraping jobs.
    """
    serializer_class = ScraperJobSerializer
    
    def get_queryset(self):
        return ScraperJob.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        job = serializer.save(user=self.request.user)
        # Trigger async task here
        run_scraper_task.delay(job.id)

    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        """
        Restart a failed job.
        """
        job = self.get_object()
        job.status = 'PENDING'
        job.save()
        # Trigger async task
        run_scraper_task.delay(job.id)
        return Response({'status': 'Job restarted'})
