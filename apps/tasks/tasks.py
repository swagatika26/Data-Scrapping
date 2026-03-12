from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def run_scraper_task(job_id):
    """
    Celery task to run the scraper asynchronously.
    """
    from apps.scraper.models import ScraperJob
    from apps.scraper.services.scraper_service import ScraperService
    
    try:
        job = ScraperJob.objects.get(id=job_id)
        job.status = 'PROCESSING'
        job.save()
        
        from django.core.cache import cache
        limits = cache.get('admin_limits') or {}
        service = ScraperService()
        result = service.execute_scrape(job.url, {'retry_limit': limits.get('retry_limit', 3), 'timeout': limits.get('timeout_seconds', 30)})
        
        # Save result
        from apps.scraper.models import ScrapedData
        ScrapedData.objects.create(job=job, content=result)
        
        if result.get('error'):
             job.status = 'FAILED'
        else:
             job.status = 'COMPLETED'
        job.save()
        
    except ScraperJob.DoesNotExist:
        logger.error(f"Job {job_id} not found")
    except Exception as e:
        logger.error(f"Error scraping job {job_id}: {str(e)}")
        if job:
            job.status = 'FAILED'
            job.save()
