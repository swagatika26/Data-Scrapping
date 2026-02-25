"""
URL configuration for oneclick_datascrape project.
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home, dashboard, signup, login_page, admin_login, logout_view, new_scrape, scrape_progress, scraped_results, history, settings_page, settings_section, run_scrape_api, export_results, delete_scrape, delete_bulk_scrapes, update_profile, update_password, download_invoice, search_proxy, admin_dashboard, admin_dashboard_section, admin_user_toggle_active, admin_user_toggle_ban, admin_user_change_role, admin_user_delete, admin_job_delete, admin_job_retry, admin_job_logs, admin_profile_update, admin_rotate_token, admin_toggle_2fa, admin_audit_report, admin_logout_all, admin_export_users, admin_create_user, admin_system_toggle_autoscale, admin_billing_run, admin_billing_export, admin_billing_request_payout, admin_settings_toggle_maintenance, admin_settings_toggle_email_alerts, admin_settings_toggle_auto_retry, admin_settings_toggle_theme, admin_settings_rotate_webhook, admin_settings_save_limits, admin_settings_save_alerts, admin_settings_reset, admin_error_logs_export, admin_error_logs_rerun_failed, admin_support_assign, admin_support_escalate, admin_support_resolve, admin_support_reply

urlpatterns = [
    path('', home, name='home'),
    path("admin/", admin.site.urls),
    path('signup/', signup, name='signup'),
    path('login/', login_page, name='login'), # Using custom view for login page
    path('admin-login/', admin_login, name='admin_login'),
    path('logout/', logout_view, name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
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
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/section/<str:section>/', admin_dashboard_section, name='admin_dashboard_section'),
    path('admin-dashboard/users/<int:user_id>/toggle-active/', admin_user_toggle_active, name='admin_user_toggle_active'),
    path('admin-dashboard/users/<int:user_id>/toggle-ban/', admin_user_toggle_ban, name='admin_user_toggle_ban'),
    path('admin-dashboard/users/<int:user_id>/change-role/', admin_user_change_role, name='admin_user_change_role'),
    path('admin-dashboard/users/<int:user_id>/delete/', admin_user_delete, name='admin_user_delete'),
    path('admin-dashboard/users/export/', admin_export_users, name='admin_export_users'),
    path('admin-dashboard/users/create/', admin_create_user, name='admin_create_user'),
    path('admin-dashboard/jobs/<int:job_id>/delete/', admin_job_delete, name='admin_job_delete'),
    path('admin-dashboard/jobs/<int:job_id>/retry/', admin_job_retry, name='admin_job_retry'),
    path('admin-dashboard/jobs/<int:job_id>/logs/', admin_job_logs, name='admin_job_logs'),
    path('admin-dashboard/profile/update/', admin_profile_update, name='admin_profile_update'),
    path('admin-dashboard/profile/rotate-token/', admin_rotate_token, name='admin_rotate_token'),
    path('admin-dashboard/profile/toggle-2fa/', admin_toggle_2fa, name='admin_toggle_2fa'),
    path('admin-dashboard/profile/audit-report/', admin_audit_report, name='admin_audit_report'),
    path('admin-dashboard/profile/logout-all/', admin_logout_all, name='admin_logout_all'),
    path('admin-dashboard/system/toggle-autoscale/', admin_system_toggle_autoscale, name='admin_system_toggle_autoscale'),
    path('admin-dashboard/billing/run/', admin_billing_run, name='admin_billing_run'),
    path('admin-dashboard/billing/export/', admin_billing_export, name='admin_billing_export'),
    path('admin-dashboard/billing/request-payout/', admin_billing_request_payout, name='admin_billing_request_payout'),
    path('admin-dashboard/settings/toggle-maintenance/', admin_settings_toggle_maintenance, name='admin_settings_toggle_maintenance'),
    path('admin-dashboard/settings/toggle-email-alerts/', admin_settings_toggle_email_alerts, name='admin_settings_toggle_email_alerts'),
    path('admin-dashboard/settings/toggle-auto-retry/', admin_settings_toggle_auto_retry, name='admin_settings_toggle_auto_retry'),
    path('admin-dashboard/settings/toggle-theme/', admin_settings_toggle_theme, name='admin_settings_toggle_theme'),
    path('admin-dashboard/settings/rotate-webhook/', admin_settings_rotate_webhook, name='admin_settings_rotate_webhook'),
    path('admin-dashboard/settings/save-limits/', admin_settings_save_limits, name='admin_settings_save_limits'),
    path('admin-dashboard/settings/save-alerts/', admin_settings_save_alerts, name='admin_settings_save_alerts'),
    path('admin-dashboard/settings/reset/', admin_settings_reset, name='admin_settings_reset'),
    path('admin-dashboard/errors/export/', admin_error_logs_export, name='admin_error_logs_export'),
    path('admin-dashboard/errors/rerun-failed/', admin_error_logs_rerun_failed, name='admin_error_logs_rerun_failed'),
    path('admin-dashboard/support/<str:ticket_id>/assign/', admin_support_assign, name='admin_support_assign'),
    path('admin-dashboard/support/<str:ticket_id>/escalate/', admin_support_escalate, name='admin_support_escalate'),
    path('admin-dashboard/support/<str:ticket_id>/resolve/', admin_support_resolve, name='admin_support_resolve'),
    path('admin-dashboard/support/<str:ticket_id>/reply/', admin_support_reply, name='admin_support_reply'),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/scraper/', include('apps.scraper.urls')),
    path('api/v1/tasks/', include('apps.tasks.urls')), # Optional, for monitoring
    # path('api/v1/exports/', include('apps.exports.urls')), # If exports have endpoints
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
