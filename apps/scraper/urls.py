from rest_framework.routers import DefaultRouter
from .views import ScraperJobViewSet

router = DefaultRouter()
router.register(r'jobs', ScraperJobViewSet, basename='scraper-job')

urlpatterns = router.urls
