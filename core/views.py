from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from apps.scraper.services.scraper_service import ScraperService
from apps.scraper.models import ScraperJob, ScrapedData
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from core.utils import search_web
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
import pandas as pd
import csv

@never_cache
def home(request):
    """
    Renders the landing page.
    """
    return render(request, 'landing_page.html')

@login_required
def history(request):
    """
    Renders the scraping history page with real data.
    """
    # Fetch real jobs for the current user
    jobs_list = ScraperJob.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply status filter if present
    status_filter = request.GET.get('status')
    if status_filter:
        jobs_list = jobs_list.filter(status=status_filter)
    
    # Pagination
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', '10')
    
    if per_page == 'all':
        paginator = Paginator(jobs_list, jobs_list.count() or 1) # Show all
    else:
        try:
            limit = int(per_page)
            if limit not in [10, 25, 50]:
                limit = 10
        except ValueError:
            limit = 10
        paginator = Paginator(jobs_list, limit)
    
    try:
        jobs = paginator.page(page)
    except PageNotAnInteger:
        jobs = paginator.page(1)
    except EmptyPage:
        jobs = paginator.page(paginator.num_pages)

    # Calculate some stats
    total_scrapes = jobs_list.count()
    # Simple estimation for storage (dummy logic for visual)
    storage_used = f"{total_scrapes * 0.5:.1f} MB" 
    
    context = {
        'jobs': jobs,
        'total_rows': total_scrapes, # using scrape count for now as proxy
        'storage_used': storage_used,
        'efficiency': '98.5%', # Placeholder
        'status_filter': status_filter,
        'per_page': per_page,
    }
    return render(request, 'dashboard/history.html', context)

@login_required
def settings_page(request):
    """
    Renders the settings page.
    """
    return render(request, 'dashboard/settings.html')

@login_required
def settings_section(request, section):
    """
    Renders the settings page and focuses on a specific section.
    Sections: profile, plan, api, privacy, security
    """
    valid_sections = {'profile', 'plan', 'api', 'privacy', 'security'}
    active_section = section if section in valid_sections else 'profile'
    
    context = {'active_section': active_section}
    
    if active_section == 'plan':
        today = timezone.now().date()
        context.update({
            'plan_name': 'PROFESSIONAL',
            'plan_price': '49.00',
            'renewal_date': (today + timedelta(days=12)).strftime('%b %d, %Y'),
            'credits_used': 8450,
            'credits_limit': 10000,
            'credits_percent': 84.5,
            'payment_methods': [
                {'type': 'Visa', 'last4': '4242', 'expiry': '12/2025', 'default': True, 'icon': 'fa-brands fa-cc-visa'},
                {'type': 'Mastercard', 'last4': '8890', 'expiry': '08/2024', 'default': False, 'icon': 'fa-brands fa-cc-mastercard'},
                {'type': 'PayPal', 'email': 'user@example.com', 'default': False, 'icon': 'fa-brands fa-paypal'},
                {'type': 'Amex', 'last4': '1005', 'expiry': '01/2026', 'default': False, 'icon': 'fa-brands fa-cc-amex'},
            ],
            'invoices': [
                {'id': '#INV-2023-009', 'date': (today - timedelta(days=15)).strftime('%b %d, %Y'), 'amount': '49.00'},
                {'id': '#INV-2023-008', 'date': (today - timedelta(days=45)).strftime('%b %d, %Y'), 'amount': '49.00'},
                {'id': '#INV-2023-007', 'date': (today - timedelta(days=75)).strftime('%b %d, %Y'), 'amount': '49.00'},
            ]
        })
    elif active_section == 'api':
        context.update({
            'api_usage': 42890,
            'api_limit': 100000,
            'api_percent': 42.9,
            'api_key': 'sk_live_51M...', # Placeholder, real key should be handled securely
            'webhooks': [
                {'url': 'https://api.yourdomain.com/hooks/scrape-complete', 'events': 'scrape.finished', 'status': 'ACTIVE'},
                {'url': 'https://webhooks.site/b92a-4122-8392', 'events': 'all_events', 'status': 'DISABLED'},
            ],
            'whitelisted_ips': ['185.220.101.44']
        })
    elif active_section == 'privacy':
        context.update({
            'anonymize_requests': True,
            'store_history': True,
            'essential_cookies': True,
            'analytics_tracking': False,
            'integrations': [
                {
                    'name': 'Google Cloud Storage',
                    'status': 'CONNECTED',
                    'status_class': 'text-brand bg-brand/10 border-brand/20',
                    'last_accessed': '2 hours ago',
                    'permission': 'Write access enabled',
                    'icon': 'fa-brands fa-google',
                    'icon_bg': 'bg-white/10 text-white'
                },
                {
                    'name': 'GitHub Actions',
                    'status': 'DISCONNECTED',
                    'status_class': 'text-gray-400 bg-white/5 border-white/10',
                    'last_accessed': 'Oct 12, 2023',
                    'permission': 'Read access only',
                    'icon': 'fa-brands fa-github',
                    'icon_bg': 'bg-white/10 text-white'
                },
                {
                    'name': 'Slack Webhooks',
                    'status': 'DISCONNECTED',
                    'status_class': 'text-gray-400 bg-white/5 border-white/10',
                    'last_accessed': 'Oct 10, 2023',
                    'permission': 'Notifications',
                    'icon': 'fa-brands fa-slack',
                    'icon_bg': 'bg-white/10 text-white'
                }
            ]
        })
    elif active_section == 'security':
        context.update({
            'last_password_change': '3 months ago',
            'two_factor_enabled': True,
            'active_sessions': [
                {
                    'id': 'sess_1',
                    'device': 'Chrome on MacOS',
                    'location': 'San Francisco, USA',
                    'ip': '192.168.1.1',
                    'is_current': True,
                    'icon': 'fa-solid fa-desktop'
                },
                {
                    'id': 'sess_2',
                    'device': 'iPhone 14 Pro',
                    'location': 'London, UK',
                    'ip': '84.17.54.215',
                    'is_current': False,
                    'icon': 'fa-solid fa-mobile-screen'
                }
            ],
            'security_logs': [
                {
                    'event': 'Successful Login',
                    'location': 'San Francisco, US',
                    'date': 'Oct 12, 2023 14:20',
                    'status': 'SUCCESS',
                    'status_class': 'text-green-400 bg-green-400/10 border-green-400/20',
                    'icon': 'fa-solid fa-arrow-right-to-bracket',
                    'icon_class': 'text-brand'
                },
                {
                    'event': 'Failed Login Attempt',
                    'location': 'Berlin, DE',
                    'date': 'Oct 11, 2023 09:15',
                    'status': 'BLOCKED',
                    'status_class': 'text-red-400 bg-red-400/10 border-red-400/20',
                    'icon': 'fa-solid fa-shield-halved',
                    'icon_class': 'text-red-400'
                },
                {
                    'event': 'Password Changed',
                    'location': 'San Francisco, US',
                    'date': 'Oct 10, 2023 18:45',
                    'status': 'SUCCESS',
                    'status_class': 'text-green-400 bg-green-400/10 border-green-400/20',
                    'icon': 'fa-solid fa-key',
                    'icon_class': 'text-brand'
                }
            ]
        })
        
    return render(request, 'dashboard/settings.html', context)

@login_required
def update_profile(request):
    """
    Handles profile updates.
    """
    if request.method == 'POST':
        user = request.user
        User = get_user_model()
        
        # Username update
        username = request.POST.get('username')
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, 'Username already taken.')
                return redirect('settings_section', section='profile')
            user.username = username

        full_name = request.POST.get('full_name')
        if full_name:
            parts = full_name.strip().split(' ', 1)
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = parts[1]
            else:
                user.last_name = ''
        
        email = request.POST.get('email')
        if email:
            user.email = email
            
        user.job_title = request.POST.get('job_title', '')
        user.location = request.POST.get('location', '')
        
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
            
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('settings_section', section='profile')
    
    return redirect('settings_section', section='profile')

@login_required
def update_password(request):
    """
    Handles password updates.
    """
    if request.method == 'POST':
        user = request.user
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not user.check_password(current_password):
            messages.error(request, 'Incorrect current password.')
            return redirect('settings_section', section='security')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('settings_section', section='security')

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Password updated successfully!')
        return redirect('settings_section', section='security')
    
    return redirect('settings_section', section='security')

@login_required
def download_invoice(request, invoice_id):
    """
    Generates and downloads a dummy invoice text file.
    """
    # Create invoice content
    today = timezone.now().strftime('%b %d, %Y')
    content = f"""
INVOICE {invoice_id}
Date: {today}
Status: PAID

Bill To:
{request.user.first_name} {request.user.last_name}
{request.user.email}

--------------------------------------------------
Description                  Amount
--------------------------------------------------
Professional Plan (Monthly)  $49.00
--------------------------------------------------
Total                        $49.00

Thank you for your business!
OneClick DataScrape
    """
    
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_id.replace("#", "")}.txt"'
    return response

@login_required
def dashboard(request):
    """
    Renders the user dashboard with real data.
    """
    # Get user's scrape jobs
    user_jobs = ScraperJob.objects.filter(user=request.user)
    
    # Calculate stats
    total_scrapes = user_jobs.count()
    successful_scrapes = user_jobs.filter(status='COMPLETED').count()
    failed_scrapes = user_jobs.filter(status='FAILED').count()
    
    # Calculate usage (assuming daily limit of 1000)
    daily_limit = 1000
    today = timezone.now().date()
    usage_today = user_jobs.filter(created_at__date=today).count()
    usage_percentage = min(int((usage_today / daily_limit) * 100), 100)
    remaining_credits = daily_limit - usage_today
    
    # Calculate time saved (Estimate: 15 mins per scrape manual vs auto)
    total_minutes_saved = total_scrapes * 15
    hours_saved = total_minutes_saved // 60
    minutes_saved = total_minutes_saved % 60
    time_saved_str = f"{hours_saved}h {minutes_saved}m"
    
    # Get recent activities
    recent_activities = user_jobs.order_by('-created_at')[:5]
    
    context = {
        'total_scrapes': total_scrapes,
        'successful_scrapes': successful_scrapes,
        'failed_scrapes': failed_scrapes,
        'time_saved': time_saved_str,
        'usage_percentage': usage_percentage,
        'usage_today': usage_today,
        'daily_limit': daily_limit,
        'remaining_credits': remaining_credits,
        'recent_activities': recent_activities,
    }
    return render(request, 'dashboard/index.html', context)

@login_required
def new_scrape(request):
    """
    Renders the 'Start New Scrape' page.
    """
    return render(request, 'dashboard/new_scrape.html')

@login_required
def scrape_progress(request):
    """
    Renders the scraping progress view.
    """
    # Get parameters from request
    url = request.GET.get('url')
    
    if not url:
        return redirect('new_scrape')
        
    url = url.strip()

    content_type = request.GET.get('content_type', 'E-commerce Products')
    export_format = request.GET.get('export_format', 'CSV')
    ai_toggle = request.GET.get('ai_toggle') == 'on'

    context = {
        'target_url': url,
        'content_type': content_type,
        'export_format': export_format,
        'ai_enabled': ai_toggle,
    }
    return render(request, 'dashboard/scrape_progress.html', context)


@login_required
def export_results(request):
    """
    Export scraped results to CSV, JSON, or Excel.
    """
    job_id = request.GET.get('job_id')
    fmt = request.GET.get('format', 'csv')
    
    if not job_id:
        return HttpResponse("Job ID required", status=400)
        
    try:
        job = ScraperJob.objects.get(id=job_id, user=request.user)
        scraped_data = ScrapedData.objects.filter(job=job).last()
        
        if not scraped_data or not scraped_data.content:
            return HttpResponse("No data found", status=404)
            
        data = scraped_data.content.get('products', [])
        
        if not data:
            return HttpResponse("No products found", status=404)
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Select and rename columns for better output
        cols = ['rank', 'name', 'price', 'url', 'status', 'date']
        # Filter to only existing columns
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
        
        if fmt == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="scrape_{job_id}.csv"'
            df.to_csv(response, index=False)
            return response
            
        elif fmt == 'json':
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="scrape_{job_id}.json"'
            df.to_json(response, orient='records', indent=2)
            return response
            
        elif fmt == 'excel' or fmt == 'xlsx':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="scrape_{job_id}.xlsx"'
            # Requires openpyxl installed
            df.to_excel(response, index=False)
            return response
            
        else:
            return HttpResponse(f"Unknown format: {fmt}", status=400)
            
    except ScraperJob.DoesNotExist:
        return HttpResponse("Job not found", status=404)
    except Exception as e:
        return HttpResponse(f"Export failed: {str(e)}", status=500)

@login_required
def search_proxy(request):
    """
    Proxy view to handle search requests and return multiple results.
    """
    query = request.GET.get('q')
    if not query:
        return JsonResponse({'error': 'No query provided'}, status=400)
    
    try:
        # Perform search using DuckDuckGo Lite (via utils)
        # We request 5 results to give the user options
        results = search_web(query, num_results=5, rich_results=True)
        
        if not results:
            return JsonResponse({'results': [], 'error': 'Search returned no results. Check your Google CSE setup (search entire web), API key, and restart the server.'})
        
        return JsonResponse({'results': results})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def run_scrape_api(request):
    """
    API endpoint to execute a scrape job.
    """
    # Manual auth check to return JSON instead of redirecting
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON body'}, status=400)

            url = data.get('url')
            
            if not url:
                return JsonResponse({'status': 'error', 'message': 'URL or Search Query is required'}, status=400)
            
            # Clean URL
            url = url.strip()

            # Handle search query (Natural Language Search)
            if not url.startswith('http'):
                search_result = search_web(url)
                if search_result:
                    url = search_result
                else:
                    return JsonResponse({'status': 'error', 'message': f'Could not find a valid URL for query: {url}'}, status=400)

            # Create job record
            job = ScraperJob.objects.create(
                user=request.user,
                url=url,
                status='PROCESSING'
            )
            
            # Execute scrape
            scraper = ScraperService()
            result = scraper.execute_scrape(url)
            
            # If the URL was changed (e.g. via search), update the job record
            if result.get('url') and result['url'] != url:
                job.url = result['url']
                job.save()
            
            # Update job
            if result.get('error'):
                job.status = 'FAILED'
                job.save()
                return JsonResponse({
                    'status': 'error', 
                    'message': result.get('error')
                })
            elif result.get('count', 0) == 0:
                # Even if no technical error, 0 items is a "logical" failure for the user
                job.status = 'FAILED'
                job.save()
                return JsonResponse({
                    'status': 'error', 
                    'message': 'No data could be extracted from this page. It might be protected or empty.'
                })
            else:
                job.status = 'COMPLETED'
                
                # Save data
                ScrapedData.objects.create(
                    job=job,
                    content=result
                )
            
            job.save()
            
            return JsonResponse({
                'status': 'success', 
                'job_id': job.id,
                'result': result
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
def scraped_results(request):
    """
    Renders the scraped search results page.
    """
    job_id = request.GET.get('job_id')
    
    if job_id:
        try:
            job = ScraperJob.objects.get(id=job_id, user=request.user)
            # Get latest data
            data_obj = job.data.last()
            scraped_data = data_obj.content if data_obj else {}
            url = job.url
        except ScraperJob.DoesNotExist:
            messages.error(request, "Job not found.")
            return redirect('history')
    else:
        # No job ID provided, redirect to history or dashboard
        messages.warning(request, "No scrape job specified.")
        return redirect('history')
    
    context = {
        'target_url': url,
        'scraped_data': scraped_data,
        'count': scraped_data.get('count', 0),
        'page_title': scraped_data.get('title', 'Scraped Results'),
        'job_id': job_id, # Pass job_id for export
    }

    # Pagination logic
    all_products = scraped_data.get('products', [])
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', '10')
    
    if per_page == 'all':
        paginator = Paginator(all_products, len(all_products) or 1) # Show all
    else:
        try:
            limit = int(per_page)
            if limit not in [10, 25, 50]:
                limit = 10
        except ValueError:
            limit = 10
        paginator = Paginator(all_products, limit)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
        
    context['products'] = products
    context['per_page'] = per_page
    
    return render(request, 'dashboard/scraped_results.html', context)

@login_required
def delete_scrape(request, job_id):
    """
    Deletes a scrape job and its associated data.
    """
    if request.method == 'POST':
        try:
            job = ScraperJob.objects.get(id=job_id, user=request.user)
            job.delete()
            messages.success(request, 'Scrape job deleted successfully.')
        except ScraperJob.DoesNotExist:
            messages.error(request, 'Job not found.')
    else:
        messages.warning(request, 'Invalid request method.')
    
    return redirect('history')

@login_required
def delete_bulk_scrapes(request):
    """
    Deletes multiple scrape jobs.
    """
    if request.method == 'POST':
        try:
            # Try to get data from JSON body first (for fetch API)
            try:
                import json
                data = json.loads(request.body)
                job_ids = data.get('job_ids', [])
            except json.JSONDecodeError:
                # Fallback to form data
                job_ids = request.POST.getlist('job_ids[]')
                if not job_ids:
                    job_ids = request.POST.getlist('job_ids')
            
            if job_ids:
                # Filter by user to ensure they only delete their own jobs
                jobs = ScraperJob.objects.filter(id__in=job_ids, user=request.user)
                count = jobs.count()
                jobs.delete()
                
                return JsonResponse({'status': 'success', 'message': f'{count} jobs deleted successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'No jobs selected.'}, status=400)
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return redirect('history')

def signup(request):
    """
    Renders the signup page.
    """
    return render(request, 'auth/signup.html')

def login_page(request):
    """
    Renders the login page and handles authentication.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            
    return render(request, 'auth/login.html')
