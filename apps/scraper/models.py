from django.db import models
from django.conf import settings

class ScraperJob(models.Model):
    """
    Model to track scraping jobs.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.url} - {self.status}"

class ScrapedData(models.Model):
    """
    Model to store scraped data.
    """
    job = models.ForeignKey(ScraperJob, on_delete=models.CASCADE, related_name='data')
    content = models.JSONField() # Using JSONField for flexibility (MongoDB)
    scraped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Data for Job {self.job_id}"
