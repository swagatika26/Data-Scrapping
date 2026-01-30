from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from apps.scraper.services.scraper_service import ScraperService
from apps.scraper.models import ScraperJob, ScrapedData
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from core.utils import search_web
import json
import pandas as pd
import csv

@never_cache
def home(request):
    """
    Renders the landing page.
    """
    return render(request, 'index.html')

@login_required
def history(request):
    """
    Renders the scraping history page with real data.
    """
    # Fetch real jobs for the current user
    jobs = ScraperJob.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate some stats
    total_scrapes = jobs.count()
    # Simple estimation for storage (dummy logic for visual)
    storage_used = f"{total_scrapes * 0.5:.1f} MB" 
    
    context = {
        'jobs': jobs,
        'total_rows': total_scrapes, # using scrape count for now as proxy
        'storage_used': storage_used,
        'efficiency': '98.5%', # Placeholder
    }
    return render(request, 'dashboard/history.html', context)

@login_required
def settings_page(request):
    """
    Renders the settings page.
    """
    return render(request, 'dashboard/settings.html')

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
    
    # Get recent activities
    recent_activities = user_jobs.order_by('-created_at')[:5]
    
    context = {
        'total_scrapes': total_scrapes,
        'successful_scrapes': successful_scrapes,
        'failed_scrapes': failed_scrapes,
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
        cols = ['rank', 'name', 'price', 'url', 'status']
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
        'products': scraped_data.get('products', []),
        'count': scraped_data.get('count', 0),
        'page_title': scraped_data.get('title', 'Scraped Results'),
        'job_id': job_id, # Pass job_id for export
    }
    return render(request, 'dashboard/scraped_results.html', context)

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
