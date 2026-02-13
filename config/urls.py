"""
URL configuration for oneclick_datascrape project.
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home, dashboard, signup, login_page, new_scrape, scrape_progress, scraped_results, history, settings_page, settings_section, run_scrape_api, export_results, delete_scrape, delete_bulk_scrapes, update_profile, update_password, download_invoice, search_proxy

urlpatterns = [
    path('', home, name='home'),
    path('signup/', signup, name='signup'),
    path('login/', login_page, name='login'), # Using custom view for login page
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/history/', history, name='history'),
    path('dashboard/history/delete/<int:job_id>/', delete_scrape, name='delete_scrape'),
    path('dashboard/history/delete-bulk/', delete_bulk_scrapes, name='delete_bulk_scrapes'),
    path('dashboard/settings/', settings_page, name='settings'),
    path('dashboard/settings/profile/update/', update_profile, name='update_profile'),
    path('dashboard/settings/password/update/', update_password, name='update_password'),
    path('dashboard/settings/download-invoice/<str:invoice_id>/', download_invoice, name='download_invoice'),
    path('dashboard/settings/<str:section>/', settings_section, name='settings_section'),
    path('dashboard/new/', new_scrape, name='new_scrape'),
    path('api/search-proxy/', search_proxy, name='search_proxy'),

    path('dashboard/progress/', scrape_progress, name='scrape_progress'),
    path('dashboard/results/', scraped_results, name='scraped_results'),
    path('api/run-scrape/', run_scrape_api, name='run_scrape_api'),
    path('api/export-results/', export_results, name='export_results'),
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/scraper/', include('apps.scraper.urls')),
    path('api/v1/tasks/', include('apps.tasks.urls')), # Optional, for monitoring
    # path('api/v1/exports/', include('apps.exports.urls')), # If exports have endpoints
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
