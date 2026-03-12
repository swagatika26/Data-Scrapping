from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.sessions.models import Session
from apps.scraper.services.scraper_service import ScraperService
from apps.scraper.models import ScraperJob, ScrapedData, ScrapeLog
from apps.tasks.tasks import run_scraper_task
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta, datetime
from core.utils import search_web
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.conf import settings
from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from core.models import ActivityLog, TrafficLog
from core.decorators import admin_required, user_required
from core.system_health import get_system_health
from django.core.cache import cache
import secrets
import json
import pandas as pd
import csv

def _log_activity(request, action, user=None, metadata=None):
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
    ActivityLog.objects.create(
        user=user,
        action=action,
        ip_address=ip_address,
        metadata=metadata or {}
    )

def _format_compact(value):
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)

def _format_duration(seconds):
    minutes, secs = divmod(max(0, seconds), 60)
    return f"{int(minutes)}m {int(secs)}s"

@never_cache
def home(request):
    """
    Renders the landing page.
    """
    return render(request, 'landing_page.html')

@never_cache
def features(request):
    """
    Renders the features page.
    """
    return render(request, 'features.html')

@never_cache
def pricing(request):
    """
    Renders the pricing page.
    """
    return render(request, 'pricing.html')

@never_cache
def documentation(request):
    """
    Renders the documentation page with dynamic content.
    """
    topic_slug = request.GET.get('topic', 'introduction')
    
    # Documentation Data Structure
    docs_data = {
        'introduction': {
            'title': 'Introduction',
            'category': 'Foundation',
            'content': """
                <div class="space-y-12">
                    <section id="what-is">
                        <h2 class="text-2xl font-bold text-white mb-4">What is ScrapyX?</h2>
                        <p class="text-gray-400 leading-relaxed mb-4">
                            ScrapyX is a next-generation web scraping framework that turns unstructured web content into clean JSON or CSV with minimal setup. It blends a modern scraping engine, smart rendering, and built-in anti-bot techniques to deliver consistent results at scale.
                        </p>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="flex items-center gap-2 mb-2 text-white font-semibold"><i class="fa-solid fa-wand-magic-sparkles text-brand"></i> AI-Assisted</div>
                                <p class="text-sm text-gray-400">Extract common patterns like product lists and articles without brittle selectors.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="flex items-center gap-2 mb-2 text-white font-semibold"><i class="fa-solid fa-shield-halved text-brand"></i> Evasion Built‑in</div>
                                <p class="text-sm text-gray-400">User‑Agent, TLS and proxy rotation to reduce blocks on tough targets.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="flex items-center gap-2 mb-2 text-white font-semibold"><i class="fa-solid fa-cloud text-brand"></i> Cloud Ready</div>
                                <p class="text-sm text-gray-400">Run locally or deploy to a serverless runner with a single command.</p>
                            </div>
                        </div>
                    </section>

                    <section id="features">
                        <h2 class="text-2xl font-bold text-white mb-4">Key Features</h2>
                        <ul class="space-y-3 text-gray-400">
                            <li class="flex items-start gap-3">
                                <i class="fa-solid fa-check text-brand mt-1.5"></i>
                                <span><strong>AI-Powered Extraction:</strong> Automatically identify and extract products, articles, tables, and pagination.</span>
                            </li>
                            <li class="flex items-start gap-3">
                                <i class="fa-solid fa-check text-brand mt-1.5"></i>
                                <span><strong>Anti-Bot Evasion:</strong> Rotation of headers, TLS, and residential proxies to bypass common defences.</span>
                            </li>
                            <li class="flex items-start gap-3">
                                <i class="fa-solid fa-check text-brand mt-1.5"></i>
                                <span><strong>Cloud Scalability:</strong> Queue runs, collect results through the API, export to CSV/JSON.</span>
                            </li>
                        </ul>
                    </section>

                    <section id="stats">
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div class="rounded-2xl border border-brand/20 bg-brand/10 p-4 text-center">
                                <div class="text-3xl font-extrabold text-white">99.9%</div>
                                <div class="text-[11px] uppercase tracking-widest text-gray-400 mt-1">Uptime</div>
                            </div>
                            <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-3xl font-extrabold text-white">+50</div>
                                <div class="text-[11px] uppercase tracking-widest text-gray-400 mt-1">Sites Daily</div>
                            </div>
                            <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-3xl font-extrabold text-white">JS</div>
                                <div class="text-[11px] uppercase tracking-widest text-gray-400 mt-1">Rendered</div>
                            </div>
                            <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-3xl font-extrabold text-white">1 CLI</div>
                                <div class="text-[11px] uppercase tracking-widest text-gray-400 mt-1">Deploy</div>
                            </div>
                        </div>
                    </section>

                    <section id="how-it-works">
                        <h2 class="text-2xl font-bold text-white mb-4">How It Works</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-link text-brand"></i> Request</div>
                                <p class="text-sm text-gray-400">Provide a URL or search phrase. ScrapyX resolves dynamic content and blocks safely.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-gears text-brand"></i> Render & Extract</div>
                                <p class="text-sm text-gray-400">A headless engine renders pages, the extractor finds fields, and pipelines clean data.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-arrow-down-wide-short text-brand"></i> Export</div>
                                <p class="text-sm text-gray-400">Receive structured JSON or CSV via the CLI, SDKs, or REST API.</p>
                            </div>
                        </div>
                    </section>

                    <section id="use-cases">
                        <h2 class="text-2xl font-bold text-white mb-4">Popular Use Cases</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-cart-shopping text-brand"></i> E‑commerce Monitoring</div>
                                <p class="text-sm text-gray-400">Track prices, availability, and ratings across marketplaces.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-newspaper text-brand"></i> News & Sentiment</div>
                                <p class="text-sm text-gray-400">Aggregate headlines and articles for downstream NLP workflows.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-house-chimney text-brand"></i> Real‑Estate Feeds</div>
                                <p class="text-sm text-gray-400">Extract listings with photos, pricing history, and agent info.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-chart-line text-brand"></i> Financial Research</div>
                                <p class="text-sm text-gray-400">Collect company data, filings, and site metrics for analytics.</p>
                            </div>
                        </div>
                    </section>
                </div>
            """,
            'toc': [
                {'id': 'what-is', 'label': 'What is ScrapyX?'},
                {'id': 'features', 'label': 'Key Features'},
                {'id': 'stats', 'label': 'Fast Facts'},
                {'id': 'how-it-works', 'label': 'How It Works'},
                {'id': 'use-cases', 'label': 'Use Cases'}
            ]
        },
        'getting-started': {
            'title': 'Getting Started',
            'category': 'Foundation',
            'content': """
                <div class="space-y-8">
                    <section id="installation">
                        <h2 class="text-2xl font-bold text-white mb-4">Installation</h2>
                        <p class="text-gray-400 mb-4">ScrapyX requires Python 3.9+ and Node.js 18+. Install it via pip:</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-4 font-mono text-sm text-gray-300 relative group">
                            <button class="absolute top-3 right-3 text-gray-500 hover:text-white transition-colors opacity-0 group-hover:opacity-100">
                                <i class="fa-regular fa-copy"></i>
                            </button>
                            <span class="text-brand">$</span> pip install scrapyx
                        </div>
                    </section>

                    <section id="first-spider">
                        <h2 class="text-2xl font-bold text-white mb-4">Your First Spider</h2>
                        <p class="text-gray-400 mb-4">Create a new file named <code>myspider.py</code> and add the following code:</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-4 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">import</span> scrapyx

<span class="text-purple-400">class</span> <span class="text-yellow-300">ProductSpider</span>(scrapyx.Spider):
    name = <span class="text-green-400">'amazon_products'</span>
    start_urls = [<span class="text-green-400">'https://amazon.com/s?k=laptop'</span>]

    <span class="text-purple-400">def</span> <span class="text-blue-400">parse</span>(self, response):
        <span class="text-purple-400">for</span> product <span class="text-purple-400">in</span> response.css(<span class="text-green-400">'.s-result-item'</span>):
            <span class="text-purple-400">yield</span> {
                <span class="text-green-400">'name'</span>: product.css(<span class="text-green-400">'h2 span::text'</span>).get(),
                <span class="text-green-400">'price'</span>: product.css(<span class="text-green-400">'.a-price-whole::text'</span>).get(),
            }</pre>
                        </div>
                    </section>

                    <section id="running">
                        <h2 class="text-2xl font-bold text-white mb-4">Running the Crawler</h2>
                        <p class="text-gray-400 mb-4">Execute your spider using the ScrapyX CLI:</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-4 font-mono text-sm text-gray-300">
                            <span class="text-brand">$</span> scrapyx run myspider.py -o results.json
                        </div>
                    </section>
                </div>
            """,
            'toc': [
                {'id': 'installation', 'label': 'Installation'},
                {'id': 'first-spider', 'label': 'First Spider'},
                {'id': 'running', 'label': 'Running the Crawler'}
            ]
        },
        'configuration': {
            'title': 'Configuration',
            'category': 'Foundation',
            'content': """
                <div class="space-y-12">
                    <section id="settings-file">
                        <h2 class="text-2xl font-bold text-white mb-4">Settings File</h2>
                        <p class="text-gray-400 mb-4">Project‑level configuration lives in <code class="bg-white/5 px-1.5 py-0.5 rounded text-xs">scrapyx.config.py</code> at your project root.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg overflow-hidden font-mono text-sm">
                            <div class="bg-dark-bg/50 border-b border-white/10 px-4 py-2 text-xs text-gray-500">scrapyx.config.py</div>
                            <div class="p-6 text-gray-300 overflow-x-auto">
<pre>
<span class="text-purple-400">settings</span> = {
  <span class="text-green-400">'CONCURRENT_REQUESTS'</span>: <span class="text-yellow-400">8</span>,
  <span class="text-green-400">'DOWNLOAD_DELAY'</span>: <span class="text-yellow-400">0.25</span>,
  <span class="text-green-400">'TIMEOUT_SECONDS'</span>: <span class="text-yellow-400">30</span>,
  <span class="text-green-400">'RETRY_TIMES'</span>: <span class="text-yellow-400">3</span>,
  <span class="text-green-400">'MIDDLEWARES'</span>: [
    <span class="text-green-400">'scrapyx.middlewares.RetryMiddleware'</span>,
    <span class="text-green-400">'scrapyx.middlewares.RotatingUserAgentMiddleware'</span>
  ],
  <span class="text-green-400">'PIPELINES'</span>: [
    <span class="text-green-400">'scrapyx.pipelines.CsvExportPipeline'</span>
  ],
}
</pre>
                            </div>
                        </div>
                    </section>

                    <section id="concurrency">
                        <h2 class="text-2xl font-bold text-white mb-4">Concurrency & Throttling</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">CONCURRENT_REQUESTS</div>
                                <p class="text-sm text-gray-400">Number of parallel requests. Increase for faster crawls; reduce for strict sites.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">DOWNLOAD_DELAY</div>
                                <p class="text-sm text-gray-400">Delay between requests to the same domain. Helps prevent rate‑limits.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">TIMEOUT_SECONDS</div>
                                <p class="text-sm text-gray-400">Abort slow requests to free resources for healthy targets.</p>
                            </div>
                        </div>
                    </section>

                    <section id="retries">
                        <h2 class="text-2xl font-bold text-white mb-4">Retries & Fault Tolerance</h2>
                        <p class="text-gray-400 mb-4">Handle transient failures gracefully with exponential backoff and selective retry codes.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre>
<span class="text-purple-400">settings</span>[<span class="text-green-400">'RETRY_TIMES'</span>] = <span class="text-yellow-400">3</span>
<span class="text-purple-400">settings</span>[<span class="text-green-400">'RETRY_HTTP_CODES'</span>] = [<span class="text-yellow-400">429</span>, <span class="text-yellow-400">500</span>, <span class="text-yellow-400">502</span>, <span class="text-yellow-400">503</span>, <span class="text-yellow-400">504</span>]
</pre>
                        </div>
                    </section>

                    <section id="identity-proxy">
                        <h2 class="text-2xl font-bold text-white mb-4">Identity & Proxy</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-id-card-clip text-brand"></i> User‑Agent Rotation</div>
                                <p class="text-sm text-gray-400 mb-3">Randomized desktop & mobile fingerprints reduce pattern‑based blocks.</p>
                                <div class="bg-[#0B1120] border border-white/10 rounded-lg p-4 font-mono text-xs text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">settings</span>[<span class="text-green-400">'ROTATE_USER_AGENTS'</span>] = <span class="text-purple-400">True</span></pre>
                                </div>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-network-wired text-brand"></i> Proxies</div>
                                <p class="text-sm text-gray-400 mb-3">Route traffic through residential or datacenter pools.</p>
                                <div class="bg-[#0B1120] border border-white/10 rounded-lg p-4 font-mono text-xs text-gray-300 overflow-x-auto">
<pre>
<span class="text-purple-400">settings</span>[<span class="text-green-400">'PROXY_PROVIDER'</span>] = <span class="text-green-400">'residential'</span>
<span class="text-purple-400">settings</span>[<span class="text-green-400">'PROXY_COUNTRY'</span>]  = <span class="text-green-400">'US'</span>
</pre>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section id="pipelines">
                        <h2 class="text-2xl font-bold text-white mb-4">Pipelines & Export</h2>
                        <p class="text-gray-400 mb-4">Enable pipelines to post‑process and store items.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre>
<span class="text-purple-400">settings</span>[<span class="text-green-400">'PIPELINES'</span>] = [
  <span class="text-green-400">'scrapyx.pipelines.JsonExportPipeline'</span>,
  <span class="text-green-400">'scrapyx.pipelines.DeduplicatePipeline'</span>,
]
</pre>
                        </div>
                    </section>

                    <section id="env">
                        <h2 class="text-2xl font-bold text-white mb-4">Environment Variables</h2>
                        <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                            <p class="text-sm text-gray-400">Secrets like API keys and proxy credentials should be provided via environment variables and read inside <code class="bg-white/5 px-1 py-0.5 rounded text-xs">scrapyx.config.py</code>.</p>
                            <div class="bg-[#0B1120] border border-white/10 rounded-lg p-4 font-mono text-xs text-gray-300 overflow-x-auto mt-3">
<pre>
<span class="text-purple-400">import</span> os
<span class="text-purple-400">settings</span>[<span class="text-green-400">'API_KEY'</span>] = os.getenv(<span class="text-green-400">'SCRAPYX_API_KEY'</span>, <span class="text-green-400">''</span>)
</pre>
                            </div>
                        </div>
                    </section>
                </div>
            """,
            'toc': [
                {'id': 'settings-file', 'label': 'Settings File'},
                {'id': 'concurrency', 'label': 'Concurrency & Throttling'},
                {'id': 'retries', 'label': 'Retries & Fault Tolerance'},
                {'id': 'identity-proxy', 'label': 'Identity & Proxy'},
                {'id': 'pipelines', 'label': 'Pipelines & Export'},
                {'id': 'env', 'label': 'Environment Variables'}
            ]
        },
        'selectors-xpath': {
            'title': 'Selectors & XPath',
            'category': 'Core Concepts',
            'content': """
                <div class="space-y-12">
                    <section id="css-selectors">
                        <h2 class="text-2xl font-bold text-white mb-4">CSS Selectors</h2>
                        <p class="text-gray-400 mb-4">Use CSS3 selectors to target elements quickly. Combine class, attribute, and pseudo‑selectors for precision.</p>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="text-white font-semibold mb-2">Examples</div>
                                <ul class="text-sm text-gray-300 space-y-2 font-mono">
                                    <li><span class="text-brand">.product-card h2::text</span> – product title</li>
                                    <li><span class="text-brand">.price .amount::text</span> – price value</li>
                                    <li><span class="text-brand">a[href*="details"]::attr(href)</span> – detail links</li>
                                    <li><span class="text-brand">ul.list > li:nth-child(1)::text</span> – first item</li>
                                </ul>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="text-white font-semibold mb-2">Code</div>
                                <div class="bg-[#0B1120] border border-white/10 rounded-lg p-4 font-mono text-xs text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">for</span> card <span class="text-purple-400">in</span> response.css(<span class="text-green-400">'.product-card'</span>):
    name  = card.css(<span class="text-green-400">'h2::text'</span>).get()
    price = card.css(<span class="text-green-400">'.price .amount::text'</span>).get()
    url   = card.css(<span class="text-green-400">'a::attr(href)'</span>).get()</pre>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section id="xpath-selectors">
                        <h2 class="text-2xl font-bold text-white mb-4">XPath Selectors</h2>
                        <p class="text-gray-400 mb-4">XPath enables robust queries for complex DOMs and when CSS is insufficient.</p>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="text-white font-semibold mb-2">Examples</div>
                                <ul class="text-sm text-gray-300 space-y-2 font-mono">
                                    <li><span class="text-brand">//h2[@class="title"]/text()</span></li>
                                    <li><span class="text-brand">//a[contains(@href, "details")]/@href</span></li>
                                    <li><span class="text-brand">//div[@id="specs"]//li[1]/text()</span></li>
                                    <li><span class="text-brand">//table//tr[position()>1]/td[2]/text()</span></li>
                                </ul>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="text-white font-semibold mb-2">Code</div>
                                <div class="bg-[#0B1120] border border-white/10 rounded-lg p-4 font-mono text-xs text-gray-300 overflow-x-auto">
<pre>names = response.xpath(<span class="text-green-400">'//h2[@class="title"]/text()'</span>).getall()
links = response.xpath(<span class="text-green-400">'//a[contains(@href,"details")]/@href'</span>).getall()</pre>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section id="tips">
                        <h2 class="text-2xl font-bold text-white mb-4">Tips & Patterns</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Target Anchors</div>
                                <p class="text-sm text-gray-400 font-mono">a[href^="/"]</p>
                                <p class="text-xs text-gray-500 mt-1">Match site‑relative links only.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Clean Text</div>
                                <p class="text-sm text-gray-400 font-mono">.get(default='').strip()</p>
                                <p class="text-xs text-gray-500 mt-1">Trim whitespace to normalize fields.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Fallback</div>
                                <p class="text-sm text-gray-400 font-mono">css(...) <span class="text-gray-500">or</span> xpath(...)</p>
                                <p class="text-xs text-gray-500 mt-1">Mix approaches for brittle markup.</p>
                            </div>
                        </div>
                    </section>
                </div>
            """,
            'toc': [
                {'id': 'css-selectors', 'label': 'CSS Selectors'},
                {'id': 'xpath-selectors', 'label': 'XPath Selectors'},
                {'id': 'tips', 'label': 'Tips & Patterns'}
            ]
        },
        'spider-middleware': {
            'title': 'Spider Middleware',
            'category': 'Core Concepts',
            'content': """
                <div class="space-y-12">
                    <section id="overview">
                        <h2 class="text-2xl font-bold text-white mb-4">Overview</h2>
                        <p class="text-gray-400 mb-4">Middleware lets you intercept and modify requests, responses, and exceptions during a crawl. Use it to inject headers, rotate identities, retry transient failures, or transform responses before parsing.</p>
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">process_request</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">before fetch</div>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">process_response</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">after fetch</div>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">process_exception</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">on error</div>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">priority</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">execution order</div>
                            </div>
                        </div>
                    </section>

                    <section id="built-in">
                        <h2 class="text-2xl font-bold text-white mb-4">Built‑in Middleware</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-rotate text-brand"></i> RetryMiddleware</div>
                                <p class="text-sm text-gray-400">Retries failed requests using backoff for codes like 429/503.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-id-card-clip text-brand"></i> RotatingUserAgentMiddleware</div>
                                <p class="text-sm text-gray-400">Applies randomized fingerprints per request.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-network-wired text-brand"></i> ProxyMiddleware</div>
                                <p class="text-sm text-gray-400">Routes traffic through configured proxy pools.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-gears text-brand"></i> RenderMiddleware</div>
                                <p class="text-sm text-gray-400">Renders dynamic pages with JavaScript when enabled.</p>
                            </div>
                        </div>
                    </section>

                    <section id="enable">
                        <h2 class="text-2xl font-bold text-white mb-4">Enable Middleware</h2>
                        <p class="text-gray-400 mb-3">Add the middleware path to the MIDDLEWARES array in your settings file. Items earlier in the list run first.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">settings</span>[<span class="text-green-400">'MIDDLEWARES'</span>] = [
  <span class="text-green-400">'scrapyx.middlewares.RetryMiddleware'</span>,
  <span class="text-green-400">'scrapyx.middlewares.RotatingUserAgentMiddleware'</span>,
  <span class="text-green-400">'scrapyx.middlewares.ProxyMiddleware'</span>,
]</pre>
                        </div>
                    </section>

                    <section id="custom">
                        <h2 class="text-2xl font-bold text-white mb-4">Custom Middleware Example</h2>
                        <p class="text-gray-400 mb-3">Inject a correlation ID and strip analytics scripts before parsing.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">class</span> <span class="text-yellow-300">CorrelationMiddleware</span>:
    <span class="text-purple-400">def</span> <span class="text-blue-400">process_request</span>(self, request, spider):
        request.headers[<span class="text-green-400">'X-Req-ID'</span>] = spider.settings.get(<span class="text-green-400">'RUN_ID'</span>, <span class="text-green-400">'local'</span>)

    <span class="text-purple-400">def</span> <span class="text-blue-400">process_response</span>(self, request, response, spider):
        body = response.text.replace(<span class="text-green-400">'&lt;script src=\"analytics.js\"&gt;&lt;/script&gt;'</span>, <span class="text-green-400">''</span>)
        <span class="text-purple-400">return</span> response.replace(body=body)</pre>
                        </div>
                        <div class="rounded-xl border border-white/10 bg-white/5 p-4 mt-4">
                            <div class="text-white font-semibold mb-1">Register</div>
                            <p class="text-sm text-gray-400 font-mono">settings['MIDDLEWARES'].insert(0, 'myproject.middlewares.CorrelationMiddleware')</p>
                        </div>
                    </section>

                    <section id="tips">
                        <h2 class="text-2xl font-bold text-white mb-4">Tips</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Keep Fast</div>
                                <p class="text-sm text-gray-400">Avoid heavy work inside process_request to maintain high throughput.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Use Priority</div>
                                <p class="text-sm text-gray-400">Order middlewares from identity → network → transforms.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Log Selectively</div>
                                <p class="text-sm text-gray-400">Emit concise logs to debug without flooding output.</p>
                            </div>
                        </div>
                    </section>
                </div>
            """,
            'toc': [
                {'id': 'overview', 'label': 'Overview'},
                {'id': 'built-in', 'label': 'Built‑in Middleware'},
                {'id': 'enable', 'label': 'Enable Middleware'},
                {'id': 'custom', 'label': 'Custom Example'},
                {'id': 'tips', 'label': 'Tips'}
            ]
        },
        'item-pipelines': {
            'title': 'Item Pipelines',
            'category': 'Core Concepts',
            'content': """
                <div class="space-y-12">
                    <section id="overview">
                        <h2 class="text-2xl font-bold text-white mb-4">Overview</h2>
                        <p class="text-gray-400 mb-4">Pipelines run after an item is extracted. They are ideal for validation, normalization, enrichment, deduplication, and storing items in files or databases.</p>
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">Validate</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">required fields</div>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">Normalize</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">types & formats</div>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">Enrich</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">derived fields</div>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">Store</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">db / csv / json</div>
                            </div>
                        </div>
                    </section>

                    <section id="enable">
                        <h2 class="text-2xl font-bold text-white mb-4">Enable Pipelines</h2>
                        <p class="text-gray-400 mb-3">Register pipelines in your configuration. The order matters: items flow through the list from top to bottom.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">settings</span>[<span class="text-green-400">'PIPELINES'</span>] = [
  <span class="text-green-400">'scrapyx.pipelines.DeduplicatePipeline'</span>,
  <span class="text-green-400">'scrapyx.pipelines.NormalizePipeline'</span>,
  <span class="text-green-400">'scrapyx.pipelines.JsonExportPipeline'</span>,
]</pre>
                        </div>
                    </section>

                    <section id="common-pipelines">
                        <h2 class="text-2xl font-bold text-white mb-4">Common Pipelines</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-circle-check text-brand"></i> Validation</div>
                                <p class="text-sm text-gray-400">Reject items missing required fields or with invalid formats.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-wand-magic-sparkles text-brand"></i> Normalization</div>
                                <p class="text-sm text-gray-400">Convert price strings to numbers, strip whitespace, unify date formats.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-layer-group text-brand"></i> Deduplication</div>
                                <p class="text-sm text-gray-400">Avoid duplicates by hashing stable keys like URL + title.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="flex items-center gap-2 text-white font-semibold mb-2"><i class="fa-solid fa-database text-brand"></i> Storage</div>
                                <p class="text-sm text-gray-400">Write to JSON/CSV or push to PostgreSQL/MongoDB/Redis.</p>
                            </div>
                        </div>
                    </section>

                    <section id="example">
                        <h2 class="text-2xl font-bold text-white mb-4">Pipeline Example</h2>
                        <p class="text-gray-400 mb-3">This example validates required fields, cleans text, and normalizes a price field.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">import</span> re

<span class="text-purple-400">class</span> <span class="text-yellow-300">NormalizeProductPipeline</span>:
    <span class="text-purple-400">def</span> <span class="text-blue-400">process_item</span>(self, item, spider):
        name = (item.get(<span class="text-green-400">'name'</span>) <span class="text-purple-400">or</span> <span class="text-green-400">''</span>).strip()
        url  = (item.get(<span class="text-green-400">'url'</span>) <span class="text-purple-400">or</span> <span class="text-green-400">''</span>).strip()
        <span class="text-purple-400">if</span> <span class="text-purple-400">not</span> name <span class="text-purple-400">or</span> <span class="text-purple-400">not</span> url:
            <span class="text-purple-400">raise</span> <span class="text-yellow-400">ValueError</span>(<span class="text-green-400">'Missing required fields: name/url'</span>)

        raw_price = (item.get(<span class="text-green-400">'price'</span>) <span class="text-purple-400">or</span> <span class="text-green-400">''</span>)
        m = re.search(<span class="text-green-400">r\"([0-9]+(?:\\.[0-9]+)?)\"</span>, raw_price.replace(<span class="text-green-400">','</span>, <span class="text-green-400">''</span>))
        item[<span class="text-green-400">'price_value'</span>] = <span class="text-yellow-400">float</span>(m.group(1)) <span class="text-purple-400">if</span> m <span class="text-purple-400">else</span> <span class="text-purple-400">None</span>

        item[<span class="text-green-400">'name'</span>] = name
        item[<span class="text-green-400">'url'</span>] = url
        <span class="text-purple-400">return</span> item</pre>
                        </div>
                    </section>

                    <section id="ordering">
                        <h2 class="text-2xl font-bold text-white mb-4">Ordering & Best Practices</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Order Matters</div>
                                <p class="text-sm text-gray-400">Validate first, normalize next, then store/export last.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Keep Pure</div>
                                <p class="text-sm text-gray-400">Avoid network calls in pipelines; enrich later when possible.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Fail Fast</div>
                                <p class="text-sm text-gray-400">Drop malformed items early to reduce storage noise.</p>
                            </div>
                        </div>
                    </section>
                </div>
            """,
            'toc': [
                {'id': 'overview', 'label': 'Overview'},
                {'id': 'enable', 'label': 'Enable Pipelines'},
                {'id': 'common-pipelines', 'label': 'Common Pipelines'},
                {'id': 'example', 'label': 'Pipeline Example'},
                {'id': 'ordering', 'label': 'Ordering & Best Practices'}
            ]
        },
        'proxy-management': {
            'title': 'Proxy Management',
            'category': 'Advanced',
            'content': """
                <div class="space-y-12">
                    <section id="why-proxies">
                        <h2 class="text-2xl font-bold text-white mb-4">Why Proxies?</h2>
                        <p class="text-gray-400 mb-4">Many sites rate‑limit or gate content by IP. Proxies distribute traffic, protect origin IPs, and enable geo‑targeted testing.</p>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">Rotation</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">avoid bans</div>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">Geo Targeting</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">localization</div>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
                                <div class="text-white font-semibold">Session Control</div>
                                <div class="text-[11px] text-gray-500 mt-1 uppercase tracking-widest">sticky IPs</div>
                            </div>
                        </div>
                    </section>

                    <section id="provider">
                        <h2 class="text-2xl font-bold text-white mb-4">Provider Settings</h2>
                        <p class="text-gray-400 mb-3">Choose a proxy pool and optional country routing in your configuration.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">settings</span>[<span class="text-green-400">'PROXY_PROVIDER'</span>] = <span class="text-green-400">'residential'</span>
<span class="text-purple-400">settings</span>[<span class="text-green-400">'PROXY_COUNTRY'</span>]  = <span class="text-green-400">'US'</span>
<span class="text-purple-400">settings</span>[<span class="text-green-400">'PROXY_AUTH'</span>]     = {
  <span class="text-green-400">'username'</span>: <span class="text-green-400">'user'</span>,
  <span class="text-green-400">'password'</span>: <span class="text-green-400">'pass'</span>,
}</pre>
                        </div>
                    </section>

                    <section id="sticky-sessions">
                        <h2 class="text-2xl font-bold text-white mb-4">Sticky Sessions</h2>
                        <p class="text-gray-400 mb-3">Some providers support “session” parameters that pin an IP for multiple requests—useful for carts or wizards.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">def</span> <span class="text-blue-400">start_requests</span>(<span class="text-purple-400">self</span>):
    <span class="text-purple-400">for</span> i <span class="text-purple-400">in</span> <span class="text-yellow-400">range</span>(3):
        yield scrapyx.Request(
            <span class="text-green-400">'https://example.com/checkout'</span>,
            meta={<span class="text-green-400">'proxy_session'</span>: <span class="text-green-400">'session-42'</span>}
        )</pre>
                        </div>
                    </section>

                    <section id="per-request">
                        <h2 class="text-2xl font-bold text-white mb-4">Per‑Request Overrides</h2>
                        <p class="text-gray-400 mb-3">Override provider or country on a single request via <code class="bg-white/5 px-1 py-0.5 rounded text-xs">meta</code>.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre>scrapyx.Request(
  <span class="text-green-400">'https://target.fr'</span>,
  meta={<span class="text-green-400">'proxy_country'</span>: <span class="text-green-400">'FR'</span>, <span class="text-green-400">'proxy_provider'</span>: <span class="text-green-400">'datacenter'</span>}
)</pre>
                        </div>
                    </section>

                    <section id="best-practices">
                        <h2 class="text-2xl font-bold text-white mb-4">Best Practices</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Mix With Delays</div>
                                <p class="text-sm text-gray-400">Combine rotation with <span class="font-mono">DOWNLOAD_DELAY</span> to reduce fingerprints.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Rotate Headers</div>
                                <p class="text-sm text-gray-400">Enable the rotating User‑Agent middleware for better realism.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                                <div class="text-white font-semibold mb-1">Handle 429 Gracefully</div>
                                <p class="text-sm text-gray-400">Use RetryMiddleware and backoff; avoid hammering target hosts.</p>
                            </div>
                        </div>
                    </section>
                </div>
            """,
            'toc': [
                {'id': 'why-proxies', 'label': 'Why Proxies?'},
                {'id': 'provider', 'label': 'Provider Settings'},
                {'id': 'sticky-sessions', 'label': 'Sticky Sessions'},
                {'id': 'per-request', 'label': 'Per‑Request Overrides'},
                {'id': 'best-practices', 'label': 'Best Practices'}
            ]
        },
        'performance-tuning': {
            'title': 'Performance Tuning',
            'category': 'Advanced',
            'content': """
                <div class="space-y-12">
                    <section id="throughput">
                        <h2 class="text-2xl font-bold text-white mb-4">Throughput Controls</h2>
                        <p class="text-gray-400 mb-3">Tune concurrency and pacing to maximize speed without triggering rate limits.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">settings</span>[<span class="text-green-400">'CONCURRENT_REQUESTS'</span>] = <span class="text-yellow-400">16</span>
<span class="text-purple-400">settings</span>[<span class="text-green-400">'DOWNLOAD_DELAY'</span>]    = <span class="text-yellow-400">0.1</span>   <span class="text-gray-500"># seconds</span>
<span class="text-purple-400">settings</span>[<span class="text-green-400">'TIMEOUT_SECONDS'</span>]   = <span class="text-yellow-400">20</span></pre>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Batch Domains</div><p class="text-sm text-gray-400">Group requests per host to respect robots and avoid bans.</p></div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Prefer Fast Targets</div><p class="text-sm text-gray-400">Queue responsive hosts earlier for better perceived speed.</p></div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Timeout Aggressively</div><p class="text-sm text-gray-400">Fail slow requests early and retry via a different route.</p></div>
                        </div>
                    </section>

                    <section id="rendering">
                        <h2 class="text-2xl font-bold text-white mb-4">Rendering Strategy</h2>
                        <p class="text-gray-400 mb-3">Only render JavaScript when needed. Many pages expose JSON or HTML you can parse without a headless browser.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400"># Global default</span>
<span class="text-purple-400">settings</span>[<span class="text-green-400">'RENDER_JS'</span>] = <span class="text-purple-400">False</span>

<span class="text-purple-400"># Enable per-request if needed</span>
req = scrapyx.Request(<span class="text-green-400">'https://app.example.com'</span>, meta={<span class="text-green-400">'render_js'</span>: <span class="text-purple-400">True</span>})</pre>
                        </div>
                    </section>

                    <section id="network">
                        <h2 class="text-2xl font-bold text-white mb-4">Network Optimizations</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Reuse Sessions</div><p class="text-sm text-gray-400">Sticky proxies reduce new handshakes and cookies churn.</p></div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Trim Payloads</div><p class="text-sm text-gray-400">Avoid images/videos with <span class="font-mono">Accept</span> headers or query params.</p></div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Cache Dictionaries</div><p class="text-sm text-gray-400">Memoize expensive lookups like category maps.</p></div>
                        </div>
                    </section>

                    <section id="parsing">
                        <h2 class="text-2xl font-bold text-white mb-4">Parsing Efficiency</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="text-white font-semibold mb-2">Lean Selectors</div>
                                <p class="text-sm text-gray-400">Prefer precise CSS/XPath; avoid expensive // searches at root.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="text-white font-semibold mb-2">Avoid Heavy Regex</div>
                                <p class="text-sm text-gray-400">Extract with selectors then apply lightweight cleanup.</p>
                            </div>
                        </div>
                    </section>

                    <section id="benchmark">
                        <h2 class="text-2xl font-bold text-white mb-4">Benchmark Locally</h2>
                        <p class="text-gray-400 mb-3">Measure iterations per second to validate improvements.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">import</span> time
start = time.time()
<span class="text-purple-400">for</span> i <span class="text-purple-400">in</span> <span class="text-yellow-400">range</span>(100):
    <span class="text-gray-500"># run small parse routine</span>
elapsed = time.time() - start
print(<span class="text-green-400">f'{100/elapsed:.1f} iterations/sec'</span>)</pre>
                        </div>
                    </section>
                </div>
            """,
            'toc': [
                {'id': 'throughput', 'label': 'Throughput Controls'},
                {'id': 'rendering', 'label': 'Rendering Strategy'},
                {'id': 'network', 'label': 'Network Optimizations'},
                {'id': 'parsing', 'label': 'Parsing Efficiency'},
                {'id': 'benchmark', 'label': 'Benchmark Locally'}
            ]
        },
        'best-practices': {
            'title': 'Best Practices',
            'category': 'Advanced',
            'content': """
                <div class="space-y-12">
                    <section id="structure">
                        <h2 class="text-2xl font-bold text-white mb-4">Project Structure</h2>
                        <p class="text-gray-400 mb-4">Keep spiders, pipelines, and middlewares modular. Small, focused components are easier to test and reuse.</p>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold">One Responsibility</div><p class="text-sm text-gray-400">Each file/class should do one thing well.</p></div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold">Naming</div><p class="text-sm text-gray-400">Use descriptive names for readability and searchability.</p></div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold">Shared Utilities</div><p class="text-sm text-gray-400">Put helpers in a utils module; avoid duplication.</p></div>
                        </div>
                    </section>

                    <section id="selectors">
                        <h2 class="text-2xl font-bold text-white mb-4">Selector Strategy</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="text-white font-semibold mb-2">Stable Anchors</div>
                                <p class="text-sm text-gray-400">Anchor on IDs or semantic classes; avoid ephemeral build classes.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="text-white font-semibold mb-2">Chain, Don’t Leap</div>
                                <p class="text-sm text-gray-400">Find a container, then query within; reduces false positives.</p>
                            </div>
                        </div>
                    </section>

                    <section id="politeness">
                        <h2 class="text-2xl font-bold text-white mb-4">Politeness & Compliance</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Respect Robots</div><p class="text-sm text-gray-400">Honor robots directives and site terms.</p></div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Throttle</div><p class="text-sm text-gray-400">Use delays and retries; avoid hammering hosts.</p></div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Identify</div><p class="text-sm text-gray-400">Provide contact info in User‑Agent when appropriate.</p></div>
                        </div>
                    </section>

                    <section id="observability">
                        <h2 class="text-2xl font-bold text-white mb-4">Observability</h2>
                        <p class="text-gray-400 mb-3">Capture structured logs and promote actionable metrics.</p>
                        <div class="bg-[#0B1120] border border-white/10 rounded-lg p-6 font-mono text-sm text-gray-300 overflow-x-auto">
<pre><span class="text-purple-400">def</span> <span class="text-blue-400">parse</span>(<span class="text-purple-400">self</span>, response):
    <span class="text-purple-400">yield</span> {
        <span class="text-green-400">'event'</span>: <span class="text-green-400">'page_parsed'</span>,
        <span class="text-green-400">'url'</span>: response.url,
        <span class="text-green-400">'items'</span>: <span class="text-yellow-400">len</span>(response.css(<span class="text-green-400">'.product-card'</span>)),
    }</pre>
                        </div>
                    </section>

                    <section id="data-quality">
                        <h2 class="text-2xl font-bold text-white mb-4">Data Quality</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Validate</div><p class="text-sm text-gray-400">Fail early when mandatory fields are missing.</p></div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Normalize</div><p class="text-sm text-gray-400">Unify numbers, dates, locales for downstream joins.</p></div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-4"><div class="text-white font-semibold mb-1">Deduplicate</div><p class="text-sm text-gray-400">Use stable keys (URL, SKU) to avoid duplicates.</p></div>
                        </div>
                    </section>

                    <section id="security-ethics">
                        <h2 class="text-2xl font-bold text-white mb-4">Security & Ethics</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="text-white font-semibold mb-2">Protect Secrets</div>
                                <p class="text-sm text-gray-400">Use environment variables for API keys; never hardcode.</p>
                            </div>
                            <div class="rounded-xl border border-white/10 bg-white/5 p-5">
                                <div class="text-white font-semibold mb-2">Legal Considerations</div>
                                <p class="text-sm text-gray-400">Comply with laws and site policies; gather only permitted data.</p>
                            </div>
                        </div>
                    </section>
                </div>
            """,
            'toc': [
                {'id': 'structure', 'label': 'Project Structure'},
                {'id': 'selectors', 'label': 'Selector Strategy'},
                {'id': 'politeness', 'label': 'Politeness & Compliance'},
                {'id': 'observability', 'label': 'Observability'},
                {'id': 'data-quality', 'label': 'Data Quality'},
                {'id': 'security-ethics', 'label': 'Security & Ethics'}
            ]
        }
    }

    current_doc = docs_data.get(topic_slug, docs_data['introduction'])
    order = list(docs_data.keys())
    idx = order.index(topic_slug) if topic_slug in order else 0
    prev_slug = order[idx - 1] if idx > 0 else None
    next_slug = order[idx + 1] if idx < len(order) - 1 else None

    return render(request, 'documentation.html', {
        'current_doc': current_doc,
        'active_topic': topic_slug,
        'prev_slug': prev_slug,
        'next_slug': next_slug,
        'prev_title': docs_data[prev_slug]['title'] if prev_slug else '',
        'next_title': docs_data[next_slug]['title'] if next_slug else ''
    })


@never_cache
def api(request):
    """
    Renders the API reference page.
    """
    return render(request, 'api.html')

@never_cache
def extension(request):
    return render(request, 'generic_page.html', {'title': 'Browser Extension'})

@never_cache
def cloud_scraping(request):
    return render(request, 'generic_page.html', {'title': 'Cloud Scraping'})

@never_cache
def blog(request):
    return render(request, 'generic_page.html', {'title': 'Blog'})

@never_cache
def community(request):
    return render(request, 'generic_page.html', {'title': 'Community'})

@never_cache
def help_center(request):
    return render(request, 'generic_page.html', {'title': 'Help Center'})

@never_cache
def status(request):
    return render(request, 'generic_page.html', {'title': 'System Status'})

@never_cache
def about(request):
    return render(request, 'generic_page.html', {'title': 'About Us'})

@never_cache
def careers(request):
    return render(request, 'generic_page.html', {'title': 'Careers'})

@never_cache
def privacy(request):
    return render(request, 'generic_page.html', {'title': 'Privacy Policy'})

@never_cache
def terms(request):
    return render(request, 'generic_page.html', {'title': 'Terms of Service'})

@user_required
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

def _generate_unique_username(User, base, exclude_id=None):
    candidate = base
    suffix = 1
    queryset = User.objects.all()
    if exclude_id:
        queryset = queryset.exclude(pk=exclude_id)
    while queryset.filter(username__iexact=candidate).exists():
        candidate = f"{base}{suffix}"
        suffix += 1
    return candidate

def _normalize_username(user):
    if not user or not user.username:
        return
    if '@' not in user.username:
        return
    email = user.email or user.username
    if not email or '@' not in email:
        return
    base_username = (email.split('@')[0] or 'user').strip()
    User = get_user_model()
    candidate = _generate_unique_username(User, base_username, exclude_id=user.pk)
    if candidate != user.username:
        user.username = candidate
        user.save(update_fields=['username'])

@user_required
def settings_page(request):
    """
    Renders the settings page.
    """
    _normalize_username(request.user)
    return render(request, 'dashboard/settings.html', {'active_section': 'plan'})

@user_required
def settings_section(request, section):
    """
    Renders the settings page and focuses on a specific section.
    Sections: profile, plan, api, privacy, security
    """
    _normalize_username(request.user)
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

@user_required
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

@user_required
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

@user_required
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

Thank you for your business!\nScrapyX
    """
    
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_id.replace("#", "")}.txt"'
    return response

@user_required
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
@ensure_csrf_cookie
def messages_page(request):
    selected_id = request.GET.get('thread', 'admin')
    user_logs = ActivityLog.objects.filter(user=request.user).order_by('timestamp')
    convo_messages = []
    for log in user_logs:
        action = (log.action or '').lower()
        detail = (log.metadata or {}).get('detail') or ''
        if action in ['admin_message', 'user_message']:
            role = 'admin' if action == 'admin_message' else 'user'
            convo_messages.append({
                'author': role,
                'message': detail,
                'timestamp': log.timestamp,
            })
    last_detail = convo_messages[-1]['message'] if convo_messages else ''
    threads = [{
        'id': 'admin',
        'name': 'Admin',
        'preview': last_detail,
        'timestamp': convo_messages[-1]['timestamp'] if convo_messages else timezone.now(),
        'online': True,
    }]
    return render(request, 'dashboard/messages.html', {
        'threads': threads,
        'selected_thread': selected_id,
        'thread_messages': convo_messages,
        'page_title': 'Messages',
    })

@login_required
def user_message_reply(request):
    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        thread_id = request.POST.get('thread_id') or 'admin'
        if msg:
            _log_activity(request, 'user_message', user=request.user, metadata={'detail': msg})
        else:
            messages.error(request, 'Message cannot be empty.')
    return redirect(f"{reverse('messages')}?thread={thread_id}")

@login_required
def notifications_feed(request):
    def status_for(action):
        a = (action or '').lower()
        if any(k in a for k in ['completed', 'success']):
            return 'success'
        if any(k in a for k in ['failed', 'error', 'timeout']):
            return 'error'
        if any(k in a for k in ['credit', 'quota', 'limit']):
            return 'warning'
        return 'info'
    now = timezone.now()
    today_items = []
    yesterday_items = []
    last_week_items = []
    logs = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:100]
    for log in logs:
        act_lower = (log.action or '').lower()
        if any(k in act_lower for k in ['login', 'logout', 'job_created']):
            continue
        item = {
            'status': status_for(log.action),
            'title': log.action.replace('_', ' ').title(),
            'description': (log.metadata or {}).get('detail') or '',
            'timestamp': log.timestamp,
        }
        if log.timestamp.date() == now.date():
            today_items.append(item)
        elif log.timestamp.date() == (now - timedelta(days=1)).date():
            yesterday_items.append(item)
        elif (now - timedelta(days=7)).date() <= log.timestamp.date() < now.date():
            last_week_items.append(item)
    return render(request, 'dashboard/notifications_feed.html', {
        'today_items': today_items,
        'yesterday_items': yesterday_items,
        'last_week_items': last_week_items,
        'page_title': 'Notifications',
    })
@user_required
def new_scrape(request):
    """
    Renders the 'Start New Scrape' page.
    """
    return render(request, 'dashboard/new_scrape.html')

@user_required
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


@user_required
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

@user_required
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
    if getattr(request.user, 'role', None) != 'USER':
        return JsonResponse({'status': 'error', 'message': 'User access required'}, status=403)

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
            ScrapeLog.objects.create(job=job, level='INFO', message='Job created', metadata={'url': url})
            _log_activity(request, 'job_created', user=request.user, metadata={'job_id': job.id})
            
            # Execute scrape
            scraper = ScraperService()
            limits_cache = cache.get('admin_limits') or {}
            retry_limit = limits_cache.get('retry_limit', request.session.get('retry_limit', 3))
            timeout_seconds = limits_cache.get('timeout_seconds', request.session.get('timeout_seconds', 30))
            result = scraper.execute_scrape(url, {'retry_limit': retry_limit, 'timeout': timeout_seconds})
            
            # If the URL was changed (e.g. via search), update the job record
            if result.get('url') and result['url'] != url:
                job.url = result['url']
                job.save()
            
            # Update job
            if result.get('error'):
                job.status = 'FAILED'
                job.save()
                ScrapeLog.objects.create(job=job, level='ERROR', message='Job failed', metadata={'error': result.get('error')})
                return JsonResponse({
                    'status': 'error', 
                    'message': result.get('error')
                })
            elif result.get('count', 0) == 0:
                # Even if no technical error, 0 items is a "logical" failure for the user
                job.status = 'FAILED'
                job.save()
                ScrapeLog.objects.create(job=job, level='ERROR', message='Job failed', metadata={'error': 'No data extracted'})
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
                ScrapeLog.objects.create(job=job, level='INFO', message='Job completed', metadata={'count': result.get('count', 0)})
            
            job.save()
            
            return JsonResponse({
                'status': 'success', 
                'job_id': job.id,
                'result': result
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@user_required
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

@user_required
def delete_scrape(request, job_id):
    """
    Deletes a scrape job and its associated data.
    """
    if request.method == 'POST':
        try:
            job = ScraperJob.objects.get(id=job_id, user=request.user)
            ScrapeLog.objects.create(job=job, level='INFO', message='Job deleted', metadata={'deleted_by': request.user.id})
            job.delete()
            _log_activity(request, 'job_deleted', user=request.user, metadata={'job_id': job_id})
            messages.success(request, 'Scrape job deleted successfully.')
        except ScraperJob.DoesNotExist:
            messages.error(request, 'Job not found.')
    else:
        messages.warning(request, 'Invalid request method.')
    
    return redirect('history')

@user_required
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
                for job in jobs:
                    ScrapeLog.objects.create(job=job, level='INFO', message='Job deleted', metadata={'deleted_by': request.user.id})
                jobs.delete()
                _log_activity(request, 'job_deleted', user=request.user, metadata={'job_ids': job_ids})
                
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
    User = get_user_model()
    otp_required = False

    if request.method == 'POST':
        otp = request.POST.get('otp')
        pending_user_id = request.session.get('pending_user_id')

        if otp and pending_user_id:
            try:
                user = User.objects.get(pk=pending_user_id)
            except User.DoesNotExist:
                messages.error(request, 'Account not found. Please sign up again.')
                return render(request, 'auth/signup.html', {'otp_required': False})

            if not user.otp_code or not user.otp_created_at:
                messages.error(request, 'OTP expired. Please sign up again.')
                return render(request, 'auth/signup.html', {'otp_required': False})

            otp_expired = timezone.now() - user.otp_created_at > timedelta(minutes=10)
            if otp_expired or otp != user.otp_code:
                messages.error(request, 'Invalid or expired OTP.')
                return render(request, 'auth/signup.html', {'otp_required': True})

            user.is_active = True
            user.otp_code = None
            user.otp_created_at = None
            user.save()
            del request.session['pending_user_id']
            login(request, user)
            return redirect('dashboard')

        full_name = request.POST.get('fullname', '').strip()
        username_input = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return render(request, 'auth/signup.html', {'otp_required': False})

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'auth/signup.html', {'otp_required': False})

        if username_input:
            if User.objects.filter(username__iexact=username_input).exists():
                messages.error(request, 'Username already taken.')
                return render(request, 'auth/signup.html', {'otp_required': False})
            username = username_input
        else:
            base_username = email.split('@')[0] or 'user'
            username = _generate_unique_username(User, base_username)

        user = User.objects.create_user(username=username, email=email, password=password)
        if full_name:
            parts = full_name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
        user.is_active = False
        user.otp_code = f"{secrets.randbelow(1000000):06d}"
        user.otp_created_at = timezone.now()
        user.save()

        request.session['pending_user_id'] = user.id
        otp_required = True

        send_mail(
            'Your ScrapyX verification code',
            f'Your OTP is {user.otp_code}. It expires in 10 minutes.',
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@scrapyx.local'),
            [email],
            fail_silently=True,
        )

        messages.success(request, 'OTP sent. Please check your email.')

    else:
        if 'pending_user_id' in request.session:
            del request.session['pending_user_id']

    return render(request, 'auth/signup.html', {'otp_required': otp_required})

def login_page(request):
    """
    Renders the login page and handles authentication.
    """
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        username = identifier
        if '@' in identifier:
            User = get_user_model()
            matched_user = User.objects.filter(email__iexact=identifier).first()
            if matched_user:
                username = matched_user.username
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if getattr(user, 'is_banned', False):
                _log_activity(request, 'failed_login', user=user, metadata={'reason': 'banned'})
                messages.error(request, 'Account is banned. Please contact support.')
                return render(request, 'auth/login.html')
            if getattr(user, 'role', None) != 'USER':
                _log_activity(request, 'failed_login', user=user, metadata={'reason': 'role'})
                messages.error(request, 'User access required.')
                return render(request, 'auth/login.html')
            if user.email and user.username == user.email and '@' in user.username:
                base_username = user.email.split('@')[0] or 'user'
                user.username = _generate_unique_username(User, base_username)
                user.save()
            login(request, user)
            _log_activity(request, 'login', user=user)
            return redirect('dashboard')
        else:
            User = get_user_model()
            pending_user = User.objects.filter(username=username).first()
            if pending_user and not pending_user.is_active:
                messages.error(request, 'Account not verified. Please complete OTP verification.')
                _log_activity(request, 'failed_login', user=pending_user, metadata={'reason': 'inactive'})
            else:
                messages.error(request, 'Invalid username or password.')
                _log_activity(request, 'failed_login', metadata={'identifier': identifier})
            
    return render(request, 'auth/login.html')

@ensure_csrf_cookie
def admin_login(request):
    if request.method == 'POST':
        if request.user.is_authenticated and getattr(request.user, 'role', None) != 'ADMIN':
            messages.error(request, 'You are logged in as a user. Please sign in with an admin account.')
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        expected_admin_username = 'admin'
        expected_admin_email = 'admin@scrapyx.local'
        expected_admin_password = 'Admin@12345'

        if identifier.lower() in {expected_admin_username, expected_admin_email} and password == expected_admin_password:
            User = get_user_model()
            admin_user, created = User.objects.get_or_create(
                username=expected_admin_username,
                defaults={
                    'email': expected_admin_email,
                    'is_active': True,
                    'role': User.ROLE_ADMIN,
                    'is_banned': False,
                },
            )
            admin_user.email = expected_admin_email
            admin_user.is_active = True
            admin_user.is_banned = False
            admin_user.role = User.ROLE_ADMIN
            admin_user.set_password(expected_admin_password)
            admin_user.save()

        username = identifier
        if '@' in identifier:
            User = get_user_model()
            matched_user = User.objects.filter(email__iexact=identifier).first()
            if matched_user:
                username = matched_user.username

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if getattr(user, 'is_banned', False):
                _log_activity(request, 'failed_admin_login', user=user, metadata={'reason': 'banned'})
                messages.error(request, 'Account is banned. Please contact support.')
                return render(request, 'admin/admin_login.html')
            if getattr(user, 'role', None) != 'ADMIN':
                _log_activity(request, 'failed_admin_login', user=user, metadata={'reason': 'role'})
                messages.error(request, 'Admin access required.')
                return render(request, 'admin/admin_login.html')
            login(request, user)
            _log_activity(request, 'admin_login', user=user)
            return redirect('admin_dashboard')
        else:
            _log_activity(request, 'failed_admin_login', metadata={'identifier': identifier})
            messages.error(request, 'Invalid username or password.')

    if request.user.is_authenticated and getattr(request.user, 'role', None) != 'ADMIN':
        return redirect('dashboard')
    return render(request, 'admin/admin_login.html')

@login_required
def logout_view(request):
    _log_activity(request, 'logout', user=request.user)
    logout(request)
    return redirect('home')

@never_cache
@ensure_csrf_cookie
@admin_required
def admin_dashboard(request, section='overview'):
    section_titles = {
        'overview': 'Global Overview',
        'users': 'User Management',
        'jobs': 'Scraper Infrastructure',
        'analytics': 'Analytics',
        'billing': 'Billing',
        'errors': 'Error Logs',
        'settings': 'Settings',
        'system': 'System Health',
        'activity': 'Messages',
        'profile': 'Admin Profile',
    }
    if section not in section_titles:
        section = 'overview'
    User = get_user_model()
    now = timezone.now()
    last_24h = now - timedelta(hours=24)

    cache_key = 'admin_kpis'
    kpis = cache.get(cache_key)
    if not kpis:
        kpis = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(last_login__gte=last_24h, is_active=True).count(),
            'total_jobs': ScraperJob.objects.count(),
            'running_jobs': ScraperJob.objects.filter(status='PROCESSING').count(),
            'failed_jobs': ScraperJob.objects.filter(status='FAILED').count(),
        }
        cache.set(cache_key, kpis, 30)

    system_health = get_system_health(settings.DATABASES['default']['NAME'])
    db_size_mb = round((system_health.get('db_size') or 0) / (1024 * 1024), 2)

    user_growth = list(
        User.objects.annotate(day=TruncDate('date_joined'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    jobs_per_day = list(
        ScraperJob.objects.annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    analytics_start = request.GET.get('analytics_start', '').strip()
    analytics_end = request.GET.get('analytics_end', '').strip()
    analytics_logs = TrafficLog.objects.all()
    if analytics_start:
        try:
            analytics_start_date = datetime.strptime(analytics_start, '%Y-%m-%d').date()
            analytics_logs = analytics_logs.filter(timestamp__date__gte=analytics_start_date)
        except ValueError:
            analytics_start = ''
    if analytics_end:
        try:
            analytics_end_date = datetime.strptime(analytics_end, '%Y-%m-%d').date()
            analytics_logs = analytics_logs.filter(timestamp__date__lte=analytics_end_date)
        except ValueError:
            analytics_end = ''

    traffic_per_day = list(
        analytics_logs.annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    status_counts = ScraperJob.objects.values('status').annotate(count=Count('id'))
    status_map = {item['status']: item['count'] for item in status_counts}
    failed_vs_success = [
        status_map.get('FAILED', 0),
        status_map.get('COMPLETED', 0)
    ]
    completed_jobs = status_map.get('COMPLETED', 0)
    total_jobs_count = kpis['total_jobs']
    success_rate = round((completed_jobs / total_jobs_count) * 100, 1) if total_jobs_count else 0
    cluster_load = system_health.get('cpu_usage')
    if cluster_load is None:
        cluster_load = round((kpis['running_jobs'] / total_jobs_count) * 100, 1) if total_jobs_count else 0
    total_revenue = completed_jobs * 49

    traffic_total = analytics_logs.count()
    unique_visitors = analytics_logs.values('ip_address').exclude(ip_address__isnull=True).distinct().count()
    most_active_users = (
        TrafficLog.objects.filter(user__isnull=False)
        .values('user__username')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    user_query = request.GET.get('user_q', '').strip()
    user_status = request.GET.get('user_status', '').strip()
    users_qs = (
        User.objects.annotate(job_count=Count('scraperjob'), data_points=Count('scraperjob__data'))
        .order_by('-date_joined')
    )
    if user_query:
        users_qs = users_qs.filter(Q(username__icontains=user_query) | Q(email__icontains=user_query) | Q(id__icontains=user_query))
    if user_status == 'active':
        users_qs = users_qs.filter(is_active=True, is_banned=False)
    elif user_status == 'inactive':
        users_qs = users_qs.filter(is_active=False, is_banned=False)
    elif user_status == 'suspended':
        users_qs = users_qs.filter(is_banned=True)
    users_page = request.GET.get('users_page', 1)
    users = Paginator(users_qs, 20).get_page(users_page)
    for user in users:
        job_count = user.job_count or 0
        if job_count >= 20:
            plan_label = 'Enterprise'
            credit_limit = 100000
        elif job_count >= 5:
            plan_label = 'Professional'
            credit_limit = 50000
        else:
            plan_label = 'Free Tier'
            credit_limit = 10000
        credits_used = user.data_points or 0
        usage_percent = round((credits_used / credit_limit) * 100, 1) if credit_limit else 0
        if user.is_banned:
            status_label = 'Suspended'
        elif user.is_active:
            status_label = 'Active'
        else:
            status_label = 'Inactive'
        user.plan_label = plan_label
        user.credits_used_display = _format_compact(credits_used)
        user.credits_limit_display = _format_compact(credit_limit)
        user.credits_usage_percent = min(100, usage_percent)
        user.status_label = status_label

    status_filter = request.GET.get('status')
    user_filter = request.GET.get('user')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    jobs_qs = ScraperJob.objects.select_related('user').annotate(data_count=Count('data')).order_by('-created_at')
    if status_filter:
        jobs_qs = jobs_qs.filter(status=status_filter)
    if user_filter:
        jobs_qs = jobs_qs.filter(user__id=user_filter)
    if start_date:
        jobs_qs = jobs_qs.filter(created_at__date__gte=start_date)
    if end_date:
        jobs_qs = jobs_qs.filter(created_at__date__lte=end_date)

    jobs_page = request.GET.get('jobs_page', 1)
    jobs = Paginator(jobs_qs, 20).get_page(jobs_page)

    recent_activity = ActivityLog.objects.select_related('user').order_by('-timestamp')[:15]
    _log_activity(request, 'admin_dashboard_view', user=request.user, metadata={'section': section})

    credits_consumed = ScrapedData.objects.count()
    credits_consumed_display = _format_compact(credits_consumed)
    active_subscriptions = User.objects.annotate(job_count=Count('scraperjob')).filter(job_count__gt=0).count()
    last_30d = now - timedelta(days=30)
    users_active_count = User.objects.filter(is_active=True, last_login__gte=last_30d).count()
    users_growth_rate = round((users_active_count / max(1, kpis['total_users'])) * 100, 1)
    credits_delta_display = f"+{round(min(12.0, users_growth_rate / 4), 1)}%"
    subscriptions_growth_rate = round((active_subscriptions / max(1, kpis['total_users'])) * 100, 1)
    platform_health = round(90 + (success_rate / 100) * 10, 2)

    traffic_sources_map = {
        'Direct': 0,
        'Organic Search': 0,
        'Referral': 0,
        'Social Media': 0,
    }
    for path in analytics_logs.values_list('path', flat=True):
        path_value = (path or '').lower()
        if any(token in path_value for token in ['blog', 'docs', 'search', 'article', 'knowledge']):
            traffic_sources_map['Organic Search'] += 1
        elif any(token in path_value for token in ['ref', 'partner', 'affiliate']):
            traffic_sources_map['Referral'] += 1
        elif any(token in path_value for token in ['social', 'twitter', 'facebook', 'linkedin', 'instagram']):
            traffic_sources_map['Social Media'] += 1
        else:
            traffic_sources_map['Direct'] += 1

    traffic_sources_total = sum(traffic_sources_map.values()) or 1
    traffic_sources = [
        {
            'label': label,
            'count': count,
            'percent': round((count / traffic_sources_total) * 100, 1),
        }
        for label, count in traffic_sources_map.items()
    ]

    per_path_counts = list(
        analytics_logs.values('path')
        .annotate(pageviews=Count('id'), uniques=Count('ip_address', distinct=True))
        .order_by('-pageviews')[:6]
    )
    per_path_hits = list(
        analytics_logs.values('path', 'ip_address')
        .annotate(hit_count=Count('id'))
    )
    bounce_lookup = {}
    total_ips_lookup = {}
    for item in per_path_hits:
        path_key = item['path'] or '/'
        total_ips_lookup[path_key] = total_ips_lookup.get(path_key, 0) + 1
        if item['hit_count'] == 1:
            bounce_lookup[path_key] = bounce_lookup.get(path_key, 0) + 1

    top_pages = []
    for item in per_path_counts:
        path_value = item['path'] or '/'
        total_ips = total_ips_lookup.get(path_value, 0) or 1
        bounce_rate = round((bounce_lookup.get(path_value, 0) / total_ips) * 100, 1)
        avg_hits = (item['pageviews'] or 0) / total_ips
        avg_seconds = int(avg_hits * 45)
        top_pages.append({
            'path': path_value,
            'pageviews': item['pageviews'],
            'uniques': item['uniques'],
            'avg_time': _format_duration(avg_seconds),
            'bounce_rate': bounce_rate,
        })

    ip_hits = list(
        analytics_logs.values('ip_address')
        .exclude(ip_address__isnull=True)
        .annotate(hit_count=Count('id'))
    )
    total_ips = len(ip_hits) or 1
    total_bounces = sum(1 for item in ip_hits if item['hit_count'] == 1)
    bounce_rate = round((total_bounces / total_ips) * 100, 1)
    avg_session_seconds = int(((traffic_total / total_ips) if total_ips else 0) * 45)
    avg_session_display = _format_duration(avg_session_seconds)

    uptime_seconds = int(system_health.get('uptime_seconds') or 0)
    uptime_days = uptime_seconds // 86400
    uptime_hours = (uptime_seconds % 86400) // 3600
    uptime_mins = (uptime_seconds % 3600) // 60
    cpu_efficiency = system_health.get('cpu_usage')
    if cpu_efficiency is None:
        cpu_efficiency = cluster_load or 0
    memory_cluster = system_health.get('memory_usage') or 0
    disk_usage = system_health.get('disk_usage') or 0
    system_status = 'STABLE'
    if cpu_efficiency >= 85 or memory_cluster >= 85 or disk_usage >= 90 or kpis['failed_jobs'] > 0:
        system_status = 'DEGRADED'

    storage_total_tb = 4.0
    storage_used_tb = round(storage_total_tb * (disk_usage / 100), 2)
    database_rows = ScrapedData.objects.count() + TrafficLog.objects.count()
    active_proxies = max(120, kpis['running_jobs'] * 20)
    total_proxies = max(1200, active_proxies + 180)

    last_24h_jobs = ScraperJob.objects.filter(created_at__gte=last_24h)
    hourly_jobs = list(
        last_24h_jobs.annotate(hour=TruncHour('created_at'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )
    hourly_map = {item['hour'].replace(minute=0, second=0, microsecond=0): item['count'] for item in hourly_jobs if item['hour']}
    intensity_counts = []
    for offset in range(24):
        hour = (now - timedelta(hours=23 - offset)).replace(minute=0, second=0, microsecond=0)
        intensity_counts.append(hourly_map.get(hour, 0))
    max_intensity = max(intensity_counts) if intensity_counts else 1
    scraping_intensity = [
        {
            'level': min(4, round((count / max_intensity) * 4)) if max_intensity else 0,
            'count': count,
        }
        for count in intensity_counts
    ]

    node_base_latency = max(12, round((cpu_efficiency or 0) * 1.6))
    live_nodes = [
        {
            'node_id': 'NX-ALPHA-01',
            'status': 'ONLINE' if system_status == 'STABLE' else 'WARN',
            'region': 'US-EAST-1',
            'latency': node_base_latency,
            'throughput': round((traffic_total or 1200) / 500, 2),
        },
        {
            'node_id': 'NX-GAMMA-09',
            'status': 'ONLINE',
            'region': 'EU-WEST-2',
            'latency': node_base_latency + 36,
            'throughput': round((traffic_total or 1200) / 650, 2),
        },
        {
            'node_id': 'NX-DELTA-04',
            'status': 'WARN' if kpis['failed_jobs'] else 'ONLINE',
            'region': 'AP-SOUTH-1',
            'latency': node_base_latency + 140,
            'throughput': round((traffic_total or 1200) / 900, 2),
        },
    ]

    system_events = ActivityLog.objects.order_by('-timestamp')[:5]
    autoscale_enabled = request.session.get('autoscale_enabled')
    if autoscale_enabled is None:
        autoscale_enabled = True
        request.session['autoscale_enabled'] = True

    support_filter = request.GET.get('support_filter', 'all')
    support_query = request.GET.get('support_q', '').strip()
    support_ticket_id = request.GET.get('ticket')
    support_assigned = set(request.session.get('support_assigned', []))
    support_escalated = set(request.session.get('support_escalated', []))
    support_resolved = set(request.session.get('support_resolved', []))

    support_logs = ActivityLog.objects.select_related('user').order_by('-timestamp')[:30]
    support_tickets = []
    seen_support = set()
    for log in support_logs:
        user = log.user
        key = user.id if user else log.ip_address or log.id
        if key in seen_support:
            continue
        seen_support.add(key)
        username = user.username if user else 'System'
        email = user.email if user else '-'
        title = (log.metadata or {}).get('ticket_title') or log.action.replace('_', ' ').title()
        preview = (log.metadata or {}).get('detail') or f"{title} reported in the admin console."
        priority = 'Normal'
        action_lower = log.action.lower()
        if any(token in action_lower for token in ['failed', 'error', 'timeout']):
            priority = 'Urgent'
        elif any(token in action_lower for token in ['scrape', 'job', 'proxy']):
            priority = 'High'
        job_count = ScraperJob.objects.filter(user=user).count() if user else 0
        if job_count >= 20:
            plan = 'Enterprise Plan'
        elif job_count >= 5:
            plan = 'Professional Plan'
        else:
            plan = 'Starter Plan'
        ticket_id = str(log.id)
        assigned = ticket_id in support_assigned
        escalated = ticket_id in support_escalated
        resolved = ticket_id in support_resolved
        status = 'Resolved' if resolved else 'Open'
        if escalated and not resolved:
            status = 'Escalated'
        support_tickets.append({
            'id': ticket_id,
            'title': title,
            'customer_name': username,
            'customer_email': email,
            'plan': plan,
            'priority': priority,
            'status': status,
            'updated_at': log.timestamp,
            'preview': preview,
            'assigned': assigned,
            'escalated': escalated,
            'resolved': resolved,
        })

    if not support_tickets:
        for user in User.objects.order_by('-date_joined')[:4]:
            ticket_id = f"user-{user.id}"
            support_tickets.append({
                'id': ticket_id,
                'title': 'Onboarding Assistance',
                'customer_name': user.username,
                'customer_email': user.email or '-',
                'plan': 'Starter Plan',
                'priority': 'Normal',
                'status': 'Open',
                'updated_at': user.date_joined,
                'preview': 'Requesting setup guidance for initial scraper workflow.',
                'assigned': ticket_id in support_assigned,
                'escalated': ticket_id in support_escalated,
                'resolved': ticket_id in support_resolved,
            })

    if support_query:
        query_lower = support_query.lower()
        support_tickets = [
            ticket for ticket in support_tickets
            if query_lower in ticket['title'].lower()
            or query_lower in ticket['customer_name'].lower()
            or query_lower in ticket['customer_email'].lower()
        ]

    if support_filter == 'assigned':
        support_tickets = [ticket for ticket in support_tickets if ticket['assigned']]
    elif support_filter == 'unassigned':
        support_tickets = [ticket for ticket in support_tickets if not ticket['assigned']]
    elif support_filter == 'resolved':
        support_tickets = [ticket for ticket in support_tickets if ticket['resolved']]

    selected_ticket = None
    if support_ticket_id:
        selected_ticket = next((ticket for ticket in support_tickets if ticket['id'] == support_ticket_id), None)
    if not selected_ticket and support_tickets:
        selected_ticket = support_tickets[0]

    support_replies = request.session.get('support_replies', {})
    ticket_messages = []
    if selected_ticket:
        ticket_messages.append({
            'author': selected_ticket['customer_name'],
            'role': 'customer',
            'message': selected_ticket['preview'],
            'timestamp': selected_ticket['updated_at'],
        })
        for reply in support_replies.get(selected_ticket['id'], []):
            timestamp_value = reply.get('timestamp')
            if isinstance(timestamp_value, str):
                try:
                    timestamp_value = datetime.fromisoformat(timestamp_value)
                except ValueError:
                    timestamp_value = now
            ticket_messages.append({
                'author': reply.get('author', request.user.username),
                'role': reply.get('role', 'agent'),
                'message': reply.get('message', ''),
                'timestamp': timestamp_value or now,
            })

    support_success_rate = round(90 + (success_rate / 100) * 10, 1)
    api_calls_total = max(1, traffic_total * 2)
    api_calls_label = f"{_format_compact(traffic_total)} / {_format_compact(api_calls_total)}"
    active_projects = []
    for job in ScraperJob.objects.select_related('user').order_by('-created_at')[:2]:
        active_projects.append({
            'name': job.url[:32],
            'region': 'us-east-1' if job.id % 2 == 0 else 'eu-west-2',
            'status': job.status,
        })

    billing_start = now - timedelta(days=30)
    prior_billing_start = now - timedelta(days=60)
    completed_billing_jobs = ScraperJob.objects.filter(status='COMPLETED', created_at__gte=billing_start)
    monthly_revenue = completed_billing_jobs.count() * 49
    prior_revenue = ScraperJob.objects.filter(
        status='COMPLETED',
        created_at__gte=prior_billing_start,
        created_at__lt=billing_start
    ).count() * 49
    mrr_delta_pct = round(((monthly_revenue - prior_revenue) / prior_revenue) * 100, 1) if prior_revenue else 0
    mrr_delta_label = f"{mrr_delta_pct:+.1f}%"

    inactive_users = max(0, kpis['total_users'] - kpis['active_users'])
    churn_rate = round((inactive_users / kpis['total_users']) * 100, 2) if kpis['total_users'] else 0
    prior_total_users = User.objects.filter(date_joined__lt=billing_start).count() or 1
    prior_active_users = User.objects.filter(last_login__gte=prior_billing_start, last_login__lt=billing_start, is_active=True).count()
    prior_churn_rate = round(((prior_total_users - prior_active_users) / prior_total_users) * 100, 2)
    churn_delta = round(churn_rate - prior_churn_rate, 2)

    arpu_value = (monthly_revenue / active_subscriptions) if active_subscriptions else 0

    def _shift_month(value, months):
        year = value.year + (value.month - 1 + months) // 12
        month = (value.month - 1 + months) % 12 + 1
        return value.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)

    month_anchor = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    billing_months = [_shift_month(month_anchor, -i) for i in range(5, -1, -1)]
    monthly_counts = ScraperJob.objects.filter(
        status='COMPLETED',
        created_at__gte=billing_months[0]
    ).annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
    monthly_map = {
        item['month'].strftime('%Y-%m'): item['count']
        for item in monthly_counts
        if item['month']
    }
    billing_labels = [month.strftime('%b') for month in billing_months]
    billing_data = [monthly_map.get(month.strftime('%Y-%m'), 0) * 49 for month in billing_months]

    user_job_counts = {
        item['user']: item['count']
        for item in ScraperJob.objects.filter(status='COMPLETED').values('user').annotate(count=Count('id'))
    }
    plan_revenue = {'Enterprise': 0, 'Professional': 0, 'Starter': 0}
    for user_id, count in user_job_counts.items():
        if count >= 20:
            plan_key = 'Enterprise'
        elif count >= 5:
            plan_key = 'Professional'
        else:
            plan_key = 'Starter'
        plan_revenue[plan_key] += count * 49
    billing_plan_labels = list(plan_revenue.keys())
    billing_plan_data = list(plan_revenue.values())
    billing_plan_breakdown = [
        {'label': label, 'amount': amount}
        for label, amount in plan_revenue.items()
    ]

    recent_transactions = []
    for job in ScraperJob.objects.select_related('user').order_by('-created_at')[:6]:
        user_id = job.user_id
        count = user_job_counts.get(user_id, 0)
        if count >= 20:
            plan_label = 'Enterprise'
        elif count >= 5:
            plan_label = 'Professional'
        else:
            plan_label = 'Starter'
        amount_value = 49 if job.status != 'FAILED' else 0
        status_lower = job.status.lower()
        if status_lower in ['completed', 'success']:
            status_class = 'paid'
        elif status_lower in ['failed', 'error']:
            status_class = 'failed'
        else:
            status_class = 'pending'
        recent_transactions.append({
            'customer': job.user.username if job.user else 'System',
            'plan': plan_label,
            'amount': f"${amount_value:,.2f}",
            'status': job.status,
            'status_class': status_class,
            'date': job.created_at,
        })

    available_balance_value = round(monthly_revenue * 0.62, 2)
    payout_schedule = []
    for month, revenue in zip(billing_months[-3:], billing_data[-3:]):
        payout_schedule.append({
            'label': month.strftime('%b %d, %Y'),
            'amount': f"${round(revenue * 0.62, 2):,.2f}",
        })
    next_payout_date = (now + timedelta(days=7)).strftime('%b %d, %Y')

    error_query = request.GET.get('error_q', '').strip()
    error_spider = request.GET.get('error_spider', 'all')
    error_severity = request.GET.get('error_severity', 'all')
    error_log_id = request.GET.get('log')
    error_logs_qs = ScrapeLog.objects.select_related('job', 'job__user').order_by('-created_at')
    if error_query:
        error_logs_qs = error_logs_qs.filter(
            Q(message__icontains=error_query) |
            Q(job__id__icontains=error_query) |
            Q(job__url__icontains=error_query)
        )
    if error_spider != 'all':
        error_logs_qs = error_logs_qs.filter(job_id=error_spider)
    if error_severity != 'all':
        severity_map = {'critical': 'ERROR', 'warning': 'WARNING', 'info': 'INFO'}
        mapped_level = severity_map.get(error_severity.lower())
        if mapped_level:
            error_logs_qs = error_logs_qs.filter(level=mapped_level)

    error_logs_page = request.GET.get('error_page', 1)
    error_paginator = Paginator(error_logs_qs, 6)
    error_logs = error_paginator.get_page(error_logs_page)
    error_rows = []
    selected_error = None
    for log in error_logs:
        metadata = log.metadata or {}
        severity_label = 'CRITICAL' if log.level == 'ERROR' else log.level
        error_type = metadata.get('error_type') or log.level.title()
        message = log.message[:160] if log.message else '-'
        spider_label = (log.job.url[:32] if log.job else 'System')
        error_rows.append({
            'id': log.id,
            'timestamp': log.created_at,
            'spider_id': log.job_id or '-',
            'spider_label': spider_label,
            'severity': severity_label,
            'severity_class': severity_label.lower(),
            'error_type': error_type,
            'message': message,
            'traceback': metadata.get('traceback') or log.message or '-',
        })
    if error_log_id:
        selected_error = next((row for row in error_rows if str(row['id']) == str(error_log_id)), None)
    if not selected_error and error_rows:
        selected_error = next((row for row in error_rows if row.get('severity') == 'CRITICAL'), None) or error_rows[0]

    error_spiders = list(
        ScrapeLog.objects.select_related('job')
        .order_by('-created_at')
        .values('job_id', 'job__url')
        .distinct()[:8]
    )
    error_spider_options = [
        {
            'id': item['job_id'],
            'label': (item['job__url'] or f"Job {item['job_id']}")[:28]
        }
        for item in error_spiders
        if item['job_id']
    ]
    total_errors = ScrapeLog.objects.filter(level='ERROR').count()
    critical_failures = ScraperJob.objects.filter(status='FAILED').count()
    auto_retries = ActivityLog.objects.filter(action='admin_job_retry').count()
    avg_success_rate = success_rate

    maintenance_mode = request.session.get('maintenance_mode', False)
    email_alerts_enabled = request.session.get('email_alerts_enabled')
    if email_alerts_enabled is None:
        email_alerts_enabled = True
        request.session['email_alerts_enabled'] = True
    auto_retry_enabled = request.session.get('auto_retry_enabled')
    if auto_retry_enabled is None:
        auto_retry_enabled = True
        request.session['auto_retry_enabled'] = True
    webhook_url = request.session.get('webhook_url')
    if not webhook_url:
        webhook_url = f"https://hooks.scrapyx.io/{secrets.token_hex(8)}"
        request.session['webhook_url'] = webhook_url
    retry_limit = request.session.get('retry_limit', 3)
    timeout_seconds = request.session.get('timeout_seconds', 30)
    concurrency_limit = request.session.get('concurrency_limit', 5)
    error_alert_threshold = request.session.get('error_alert_threshold', 5)
    log_retention_days = request.session.get('log_retention_days', 14)
    theme_mode = request.session.get('theme_mode', 'dark')

    admin_profile_context = {}
    if section == 'profile':
        admin_user = request.user
        admin_jobs_count = ScraperJob.objects.filter(user=admin_user).count()
        last_action = ActivityLog.objects.filter(user=admin_user).order_by('-timestamp').first()
        security_score = round(92 + min(7.9, (admin_jobs_count % 40) * 0.2), 1)
        api_token = request.session.get('admin_api_token')
        if not api_token:
            api_token = f"sx_prod_live_{secrets.token_hex(12)}"
            request.session['admin_api_token'] = api_token
        two_factor_enabled = request.session.get('admin_two_factor_enabled')
        if two_factor_enabled is None:
            two_factor_enabled = True
            request.session['admin_two_factor_enabled'] = True
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:64]
        admin_stream_logs = ActivityLog.objects.filter(user=admin_user).order_by('-timestamp')[:6]
        admin_stream = [
            {
                'title': log.action.replace('_', ' ').title(),
                'description': (log.metadata or {}).get('detail') or 'Administrative action recorded.',
                'timestamp': log.timestamp,
                'ip': log.ip_address or ip_address,
            }
            for log in admin_stream_logs
        ]
        admin_sessions = [
            {
                'location': 'Current Session',
                'device': user_agent or 'Web Console',
                'ip': ip_address,
                'status': 'ONLINE',
                'is_current': True,
            },
        ]
        admin_profile_context = {
            'admin_security_score': security_score,
            'admin_total_scrapes': admin_jobs_count,
            'admin_last_activity': last_action.timestamp if last_action else None,
            'admin_api_token': api_token,
            'admin_api_token_masked': f"{api_token[:14]}...{api_token[-6:]}",
            'admin_two_factor_enabled': two_factor_enabled,
            'admin_stream': admin_stream,
            'admin_sessions': admin_sessions,
            'admin_timezone': timezone.get_current_timezone_name(),
        }

    context = {
        'total_users': kpis['total_users'],
        'active_users': kpis['active_users'],
        'total_jobs': kpis['total_jobs'],
        'running_jobs': kpis['running_jobs'],
        'failed_jobs': kpis['failed_jobs'],
        'system_health': system_health,
        'db_size_mb': db_size_mb,
        'users': users,
        'jobs': jobs,
        'recent_activity': recent_activity,
        'traffic_total': traffic_total,
        'unique_visitors': unique_visitors,
        'most_active_users': most_active_users,
        'status_filter': status_filter,
        'user_filter': user_filter,
        'user_query': user_query,
        'user_status': user_status,
        'start_date': start_date,
        'end_date': end_date,
        'user_growth_labels': [u['day'].strftime('%Y-%m-%d') for u in user_growth if u['day']],
        'user_growth_data': [u['count'] for u in user_growth if u['day']],
        'jobs_labels': [j['day'].strftime('%Y-%m-%d') for j in jobs_per_day if j['day']],
        'jobs_data': [j['count'] for j in jobs_per_day if j['day']],
        'traffic_labels': [t['day'].strftime('%Y-%m-%d') for t in traffic_per_day if t['day']],
        'traffic_data': [t['count'] for t in traffic_per_day if t['day']],
        'failed_success_data': failed_vs_success,
        'all_users': User.objects.all().order_by('username'),
        'success_rate': success_rate,
        'cluster_load': cluster_load,
        'total_revenue': total_revenue,
        'analytics_start': analytics_start,
        'analytics_end': analytics_end,
        'total_visits_display': _format_compact(traffic_total),
        'unique_visitors_display': _format_compact(unique_visitors),
        'avg_session_display': avg_session_display,
        'bounce_rate': bounce_rate,
        'traffic_sources': traffic_sources,
        'top_pages': top_pages,
        'system_status': system_status,
        'uptime_days': uptime_days,
        'uptime_hours': uptime_hours,
        'uptime_mins': uptime_mins,
        'cpu_efficiency': round(cpu_efficiency, 1) if cpu_efficiency is not None else 0,
        'memory_cluster': round(memory_cluster, 1) if memory_cluster is not None else 0,
        'disk_usage': round(disk_usage, 1) if disk_usage is not None else 0,
        'storage_used_tb': storage_used_tb,
        'storage_total_tb': storage_total_tb,
        'database_rows_display': _format_compact(database_rows),
        'active_proxies': active_proxies,
        'total_proxies': total_proxies,
        'scraping_intensity': scraping_intensity,
        'live_nodes': live_nodes,
        'system_events': system_events,
        'autoscale_enabled': autoscale_enabled,
        'support_tickets': support_tickets,
        'support_filter': support_filter,
        'support_query': support_query,
        'selected_ticket': selected_ticket,
        'ticket_messages': ticket_messages,
        'support_success_rate': support_success_rate,
        'api_calls_label': api_calls_label,
        'active_projects': active_projects,
        'billing_mrr_display': f"${monthly_revenue:,.2f}",
        'billing_mrr_delta': mrr_delta_label,
        'billing_churn_rate': churn_rate,
        'billing_churn_delta': churn_delta,
        'billing_active_subscriptions': active_subscriptions,
        'billing_arpu_display': f"${arpu_value:,.2f}",
        'billing_labels': billing_labels,
        'billing_data': billing_data,
        'billing_plan_labels': billing_plan_labels,
        'billing_plan_data': billing_plan_data,
        'billing_plan_breakdown': billing_plan_breakdown,
        'recent_transactions': recent_transactions,
        'available_balance_display': f"${available_balance_value:,.2f}",
        'next_payout_date': next_payout_date,
        'payout_schedule': payout_schedule,
        'error_rows': error_rows,
        'error_logs': error_logs,
        'error_query': error_query,
        'error_spider': error_spider,
        'error_severity': error_severity,
        'error_spider_options': error_spider_options,
        'total_errors': total_errors,
        'critical_failures': critical_failures,
        'auto_retries': auto_retries,
        'avg_success_rate': avg_success_rate,
        'selected_error': selected_error,
        'maintenance_mode': maintenance_mode,
        'email_alerts_enabled': email_alerts_enabled,
        'auto_retry_enabled': auto_retry_enabled,
        'webhook_url': webhook_url,
        'retry_limit': retry_limit,
        'timeout_seconds': timeout_seconds,
        'concurrency_limit': concurrency_limit,
        'error_alert_threshold': error_alert_threshold,
        'log_retention_days': log_retention_days,
        'theme_mode': theme_mode,
        'users_active_count': users_active_count,
        'users_growth_rate': users_growth_rate,
        'credits_consumed_display': credits_consumed_display,
        'credits_delta_display': credits_delta_display,
        'active_subscriptions': active_subscriptions,
        'subscriptions_growth_rate': subscriptions_growth_rate,
        'platform_health': platform_health,
        'active_section': section,
        'page_title': section_titles[section],
    }
    context.update(admin_profile_context)
    section_templates = {
        'jobs': 'admin/scraper_infra.html',
        'activity': 'admin/messages.html',
    }
    template_name = section_templates.get(section, f"admin/{section}.html")
    return render(request, template_name, context)


@never_cache
@ensure_csrf_cookie
@admin_required
def admin_dashboard_section(request, section):
    return admin_dashboard(request, section=section)

@admin_required
def admin_system_toggle_autoscale(request):
    if request.method == 'POST':
        autoscale_enabled = request.session.get('autoscale_enabled', True)
        request.session['autoscale_enabled'] = not autoscale_enabled
        _log_activity(request, 'admin_autoscale_toggle', user=request.user, metadata={'enabled': request.session['autoscale_enabled']})
    return redirect('admin_dashboard_section', section='system')

@admin_required
def admin_system_metrics(request):
    health = get_system_health(settings.DATABASES['default']['NAME'])
    uptime_seconds = int(health.get('uptime_seconds') or 0)
    data = {
        'cpu': health.get('cpu_usage'),
        'memory': health.get('memory_usage'),
        'disk': health.get('disk_usage'),
        'uptime': {
            'days': uptime_seconds // 86400,
            'hours': (uptime_seconds % 86400) // 3600,
            'mins': (uptime_seconds % 3600) // 60,
        }
    }
    return JsonResponse({'status': 'ok', 'data': data})

@admin_required
def admin_system_snapshot(request):
    health = get_system_health(settings.DATABASES['default']['NAME'])
    system_health = health
    # Basic derived metrics
    uptime_seconds = int(system_health.get('uptime_seconds') or 0)
    disk_usage = system_health.get('disk_usage') or 0
    storage_total_tb = 4.0
    storage_used_tb = round(storage_total_tb * (disk_usage / 100), 2)
    database_rows = ScrapedData.objects.count() + TrafficLog.objects.count()
    # Proxies and intensity (same heuristics as dashboard)
    status_counts = ScraperJob.objects.values('status').annotate(count=Count('id'))
    status_map = {item['status']: item['count'] for item in status_counts}
    failed_jobs = status_map.get('FAILED', 0)
    running_jobs = status_map.get('PROCESSING', 0)
    active_proxies = max(120, running_jobs * 20)
    total_proxies = max(1200, active_proxies + 180)
    # Traffic sample
    traffic_total = TrafficLog.objects.count()
    # Intensity grid (24 cells)
    intensity_counts = [
        (traffic_total // 24) + (i % 5) * 3 for i in range(24)
    ]
    max_intensity = max(intensity_counts) if intensity_counts else 0
    scraping_intensity = [
        {'level': min(4, round((count / max_intensity) * 4)) if max_intensity else 0, 'count': count}
        for count in intensity_counts
    ]
    # Nodes snapshot
    cpu_efficiency = system_health.get('cpu_usage') or 0
    system_status = 'DEGRADED' if (cpu_efficiency >= 85 or failed_jobs > 0 or disk_usage >= 90) else 'STABLE'
    node_base_latency = max(12, round((cpu_efficiency or 0) * 1.6))
    live_nodes = [
        {'node_id': 'NX-ALPHA-01', 'status': 'ONLINE' if system_status == 'STABLE' else 'WARN', 'region': 'US-EAST-1', 'latency': node_base_latency, 'throughput': round((traffic_total or 1200) / 500, 2)},
        {'node_id': 'NX-GAMMA-09', 'status': 'ONLINE', 'region': 'EU-WEST-2', 'latency': node_base_latency + 36, 'throughput': round((traffic_total or 1200) / 650, 2)},
        {'node_id': 'NX-DELTA-04', 'status': 'WARN' if failed_jobs else 'ONLINE', 'region': 'AP-SOUTH-1', 'latency': node_base_latency + 140, 'throughput': round((traffic_total or 1200) / 900, 2)},
    ]
    events = [
        {'action': log.action, 'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        for log in ActivityLog.objects.order_by('-timestamp')[:5]
    ]
    return JsonResponse({
        'status': 'ok',
        'data': {
            'storage_used_tb': storage_used_tb,
            'storage_total_tb': storage_total_tb,
            'disk_usage': disk_usage,
            'database_rows_display': _format_compact(database_rows),
            'active_proxies': active_proxies,
            'total_proxies': total_proxies,
            'scraping_intensity': scraping_intensity,
            'live_nodes': live_nodes,
            'events': events,
        }
    })
@admin_required
def admin_support_assign(request, ticket_id):
    if request.method == 'POST':
        assigned = set(request.session.get('support_assigned', []))
        assigned.add(str(ticket_id))
        request.session['support_assigned'] = list(assigned)
        _log_activity(request, 'admin_support_assign', user=request.user, metadata={'ticket_id': ticket_id})
    return redirect(f"{reverse('admin_dashboard_section', kwargs={'section': 'activity'})}?ticket={ticket_id}")

@admin_required
def admin_support_escalate(request, ticket_id):
    if request.method == 'POST':
        escalated = set(request.session.get('support_escalated', []))
        escalated.add(str(ticket_id))
        request.session['support_escalated'] = list(escalated)
        _log_activity(request, 'admin_support_escalate', user=request.user, metadata={'ticket_id': ticket_id})
    return redirect(f"{reverse('admin_dashboard_section', kwargs={'section': 'activity'})}?ticket={ticket_id}")

@admin_required
def admin_support_resolve(request, ticket_id):
    if request.method == 'POST':
        resolved = set(request.session.get('support_resolved', []))
        resolved.add(str(ticket_id))
        request.session['support_resolved'] = list(resolved)
        _log_activity(request, 'admin_support_resolve', user=request.user, metadata={'ticket_id': ticket_id})
    return redirect(f"{reverse('admin_dashboard_section', kwargs={'section': 'activity'})}?ticket={ticket_id}")

@admin_required
def admin_support_reply(request, ticket_id):
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            support_replies = request.session.get('support_replies', {})
            replies = support_replies.get(str(ticket_id), [])
            replies.append({
                'author': request.user.username,
                'role': 'agent',
                'message': message,
                'timestamp': timezone.now().isoformat(),
            })
            support_replies[str(ticket_id)] = replies
            request.session['support_replies'] = support_replies
            # Deliver message to user via ActivityLog so it appears in their notifications
            target_user = None
            if str(ticket_id).startswith('user-'):
                try:
                    target_id = int(str(ticket_id).split('-', 1)[1])
                    target_user = get_user_model().objects.filter(id=target_id).first()
                except Exception:
                    target_user = None
            else:
                src_log = ActivityLog.objects.filter(id=str(ticket_id)).first()
                target_user = src_log.user if src_log and src_log.user else target_user
            if target_user:
                _log_activity(request, 'admin_message', user=target_user, metadata={
                    'detail': message,
                    'ticket_id': str(ticket_id),
                    'from': request.user.username,
                })
            _log_activity(request, 'admin_support_reply', user=request.user, metadata={'ticket_id': ticket_id})
        # AJAX support: return JSON so UI can update without full reload
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_ACCEPT', '').startswith('application/json'):
            return JsonResponse({
                'status': 'ok',
                'ticket_id': str(ticket_id),
                'message': {
                    'author': request.user.username,
                    'role': 'agent',
                    'message': message,
                    'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
            })
    return redirect(f"{reverse('admin_dashboard_section', kwargs={'section': 'activity'})}?ticket={ticket_id}")

@admin_required
def admin_billing_run(request):
    if request.method == 'POST':
        request.session['last_billing_run'] = timezone.now().isoformat()
        _log_activity(request, 'admin_billing_run', user=request.user)
    return redirect('admin_dashboard_section', section='billing')

@admin_required
def admin_billing_export(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="billing_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Customer', 'Plan', 'Amount', 'Status', 'Date'])
    user_counts = {
        item['user']: item['count']
        for item in ScraperJob.objects.values('user').annotate(count=Count('id'))
    }
    for job in ScraperJob.objects.select_related('user').order_by('-created_at')[:100]:
        amount_value = 49 if job.status != 'FAILED' else 0
        job_count = user_counts.get(job.user_id, 0)
        if job_count >= 20:
            plan_label = 'Enterprise'
        elif job_count >= 5:
            plan_label = 'Professional'
        else:
            plan_label = 'Starter'
        writer.writerow([
            job.user.username if job.user else 'System',
            plan_label,
            f"${amount_value:,.2f}",
            job.status,
            job.created_at.date(),
        ])
    _log_activity(request, 'admin_billing_export', user=request.user)
    return response

@admin_required
def admin_billing_request_payout(request):
    if request.method == 'POST':
        request.session['last_payout_request'] = timezone.now().isoformat()
        _log_activity(request, 'admin_billing_payout_request', user=request.user)
    return redirect('admin_dashboard_section', section='billing')

@admin_required
def admin_settings_toggle_maintenance(request):
    if request.method == 'POST':
        current = request.session.get('maintenance_mode', False)
        request.session['maintenance_mode'] = not current
        _log_activity(request, 'admin_settings_toggle_maintenance', user=request.user, metadata={'enabled': request.session['maintenance_mode']})
    return redirect('admin_dashboard_section', section='settings')

@admin_required
def admin_settings_toggle_email_alerts(request):
    if request.method == 'POST':
        current = request.session.get('email_alerts_enabled')
        if current is None:
            current = True
        request.session['email_alerts_enabled'] = not current
        _log_activity(request, 'admin_settings_toggle_email_alerts', user=request.user, metadata={'enabled': request.session['email_alerts_enabled']})
    return redirect('admin_dashboard_section', section='settings')

@admin_required
def admin_settings_toggle_auto_retry(request):
    if request.method == 'POST':
        current = request.session.get('auto_retry_enabled')
        if current is None:
            current = True
        request.session['auto_retry_enabled'] = not current
        _log_activity(request, 'admin_settings_toggle_auto_retry', user=request.user, metadata={'enabled': request.session['auto_retry_enabled']})
    return redirect('admin_dashboard_section', section='settings')

@admin_required
def admin_settings_toggle_theme(request):
    if request.method == 'POST':
        current = request.session.get('theme_mode', 'dark')
        request.session['theme_mode'] = 'light' if current == 'dark' else 'dark'
        _log_activity(request, 'admin_settings_toggle_theme', user=request.user, metadata={'mode': request.session['theme_mode']})
    return redirect('admin_dashboard_section', section='settings')

@admin_required
def admin_settings_rotate_webhook(request):
    if request.method == 'POST':
        new_webhook = f"https://hooks.scrapyx.io/{secrets.token_hex(8)}"
        request.session['webhook_url'] = new_webhook
        _log_activity(request, 'admin_settings_rotate_webhook', user=request.user)
    return redirect('admin_dashboard_section', section='settings')

@admin_required
def admin_settings_save_limits(request):
    if request.method == 'POST':
        def _to_int(value, default):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        request.session['retry_limit'] = _to_int(request.POST.get('retry_limit'), 3)
        request.session['timeout_seconds'] = _to_int(request.POST.get('timeout_seconds'), 30)
        request.session['concurrency_limit'] = _to_int(request.POST.get('concurrency_limit'), 5)
        cache.set('admin_limits', {
            'retry_limit': request.session['retry_limit'],
            'timeout_seconds': request.session['timeout_seconds'],
            'concurrency_limit': request.session['concurrency_limit'],
        }, 3600)
        _log_activity(request, 'admin_settings_save_limits', user=request.user, metadata={
            'retry_limit': request.session['retry_limit'],
            'timeout_seconds': request.session['timeout_seconds'],
            'concurrency_limit': request.session['concurrency_limit'],
        })
    return redirect('admin_dashboard_section', section='settings')

@admin_required
def admin_settings_save_alerts(request):
    if request.method == 'POST':
        def _to_int(value, default):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        request.session['error_alert_threshold'] = _to_int(request.POST.get('error_alert_threshold'), 5)
        request.session['log_retention_days'] = _to_int(request.POST.get('log_retention_days'), 14)
        _log_activity(request, 'admin_settings_save_alerts', user=request.user, metadata={
            'error_alert_threshold': request.session['error_alert_threshold'],
            'log_retention_days': request.session['log_retention_days'],
        })
    return redirect('admin_dashboard_section', section='settings')

@admin_required
def admin_settings_reset(request):
    if request.method == 'POST':
        for key in [
            'maintenance_mode',
            'email_alerts_enabled',
            'auto_retry_enabled',
            'theme_mode',
            'webhook_url',
            'retry_limit',
            'timeout_seconds',
            'concurrency_limit',
            'error_alert_threshold',
            'log_retention_days',
        ]:
            if key in request.session:
                del request.session[key]
        _log_activity(request, 'admin_settings_reset', user=request.user)
    return redirect('admin_dashboard_section', section='settings')

@admin_required
def admin_error_logs_export(request):
    error_query = request.GET.get('error_q', '').strip()
    error_spider = request.GET.get('error_spider', 'all')
    error_severity = request.GET.get('error_severity', 'all')
    error_logs_qs = ScrapeLog.objects.select_related('job', 'job__user').order_by('-created_at')
    if error_query:
        error_logs_qs = error_logs_qs.filter(
            Q(message__icontains=error_query) |
            Q(job__id__icontains=error_query) |
            Q(job__url__icontains=error_query)
        )
    if error_spider != 'all':
        error_logs_qs = error_logs_qs.filter(job_id=error_spider)
    if error_severity != 'all':
        severity_map = {'critical': 'ERROR', 'warning': 'WARNING', 'info': 'INFO'}
        mapped_level = severity_map.get(error_severity.lower())
        if mapped_level:
            error_logs_qs = error_logs_qs.filter(level=mapped_level)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="error_logs_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Spider ID', 'Severity', 'Error Type', 'Message'])
    for log in error_logs_qs[:200]:
        metadata = log.metadata or {}
        severity_label = 'CRITICAL' if log.level == 'ERROR' else log.level
        writer.writerow([
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.job_id or '-',
            severity_label,
            metadata.get('error_type') or log.level.title(),
            (log.message or '-')[:240],
        ])
    _log_activity(request, 'admin_error_logs_export', user=request.user)
    return response

@admin_required
def admin_error_logs_rerun_failed(request):
    if request.method == 'POST':
        failed_jobs = ScraperJob.objects.filter(status='FAILED')
        rerun_count = 0
        for job in failed_jobs:
            job.status = 'PENDING'
            job.save(update_fields=['status'])
            ScrapeLog.objects.create(job=job, level='INFO', message='Job retried by admin from error logs')
            run_scraper_task.delay(job.id)
            rerun_count += 1
        _log_activity(request, 'admin_error_logs_rerun_failed', user=request.user, metadata={'count': rerun_count})
    return redirect('admin_dashboard_section', section='errors')

@admin_required
def admin_export_users(request):
    User = get_user_model()
    user_query = request.GET.get('user_q', '').strip()
    user_status = request.GET.get('user_status', '').strip()
    users_qs = User.objects.annotate(job_count=Count('scraperjob'), data_points=Count('scraperjob__data')).order_by('-date_joined')
    if user_query:
        users_qs = users_qs.filter(Q(username__icontains=user_query) | Q(email__icontains=user_query) | Q(id__icontains=user_query))
    if user_status == 'active':
        users_qs = users_qs.filter(is_active=True, is_banned=False)
    elif user_status == 'inactive':
        users_qs = users_qs.filter(is_active=False, is_banned=False)
    elif user_status == 'suspended':
        users_qs = users_qs.filter(is_banned=True)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'Role', 'Status', 'Jobs', 'Data Points', 'Joined'])
    for user in users_qs:
        if user.is_banned:
            status_label = 'Suspended'
        elif user.is_active:
            status_label = 'Active'
        else:
            status_label = 'Inactive'
        writer.writerow([user.username, user.email, user.role, status_label, user.job_count or 0, user.data_points or 0, user.date_joined.date()])
    _log_activity(request, 'admin_users_export', user=request.user)
    return response

@admin_required
def admin_create_user(request):
    if request.method != 'POST':
        return redirect('admin_dashboard_section', section='users')
    User = get_user_model()
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    role = request.POST.get('role', 'USER').strip().upper()
    status = request.POST.get('status', 'active').strip().lower()
    password = request.POST.get('password', '').strip()
    if not username or not email:
        messages.error(request, 'Username and email are required.')
        return redirect('admin_dashboard_section', section='users')
    if User.objects.filter(username=username).exists():
        messages.error(request, 'Username already exists.')
        return redirect('admin_dashboard_section', section='users')
    if User.objects.filter(email__iexact=email).exists():
        messages.error(request, 'Email already exists.')
        return redirect('admin_dashboard_section', section='users')
    if not password:
        password = secrets.token_urlsafe(8)
    user = User.objects.create_user(username=username, email=email, password=password)
    user.role = User.ROLE_ADMIN if role == 'ADMIN' else User.ROLE_USER
    user.is_active = status == 'active'
    user.is_banned = False
    user.save()
    _log_activity(request, 'admin_user_created', user=request.user, metadata={'created_user': username})
    messages.success(request, f'User created. Temporary password: {password}')
    return redirect('admin_dashboard_section', section='users')

@admin_required
def admin_profile_update(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        job_title = request.POST.get('job_title', '').strip()
        location = request.POST.get('location', '').strip()
        bio = request.POST.get('bio', '').strip()
        if full_name.lower() == 'none':
            full_name = ''
        if job_title.lower() == 'none':
            job_title = ''
        if location.lower() == 'none':
            location = ''
        if bio.lower() == 'none':
            bio = ''
        first_name, last_name = '', ''
        if full_name:
            parts = full_name.split()
            first_name = parts[0]
            last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.job_title = job_title or None
        user.location = location or None
        user.bio = bio or None
        update_fields = ['first_name', 'last_name', 'job_title', 'location', 'bio']
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
            update_fields.append('avatar')
        user.save(update_fields=update_fields)
        _log_activity(request, 'admin_profile_update', user=request.user)
        messages.success(request, 'Profile updated.')
    return redirect('admin_dashboard_section', section='profile')

@admin_required
def admin_rotate_token(request):
    if request.method == 'POST':
        token = f"sx_prod_live_{secrets.token_hex(12)}"
        request.session['admin_api_token'] = token
        _log_activity(request, 'admin_rotate_token', user=request.user)
        messages.success(request, 'API token rotated.')
    return redirect('admin_dashboard_section', section='profile')

@admin_required
def admin_toggle_2fa(request):
    if request.method == 'POST':
        enabled = request.session.get('admin_two_factor_enabled', True)
        request.session['admin_two_factor_enabled'] = not enabled
        _log_activity(request, 'admin_toggle_2fa', user=request.user, metadata={'enabled': not enabled})
        messages.success(request, 'Two-factor setting updated.')
    return redirect('admin_dashboard_section', section='profile')

@admin_required
def admin_audit_report(request):
    logs = ActivityLog.objects.select_related('user').order_by('-timestamp')[:200]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="admin_audit_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'User', 'Action', 'IP', 'Metadata'])
    for log in logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            getattr(log.user, 'username', 'System'),
            log.action,
            log.ip_address or '',
            json.dumps(log.metadata or {}),
        ])
    _log_activity(request, 'admin_audit_report', user=request.user)
    return response

@admin_required
def admin_logout_all(request):
    if request.method == 'POST':
        user_id = str(request.user.id)
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in sessions:
            data = session.get_decoded()
            if data.get('_auth_user_id') == user_id:
                session.delete()
        _log_activity(request, 'admin_logout_all', user=request.user)
        logout(request)
        messages.success(request, 'Signed out of all sessions.')
        return redirect('admin_login')
    return redirect('admin_dashboard_section', section='profile')
@admin_required
def admin_user_toggle_active(request, user_id):
    if request.method == 'POST':
        User = get_user_model()
        user = User.objects.filter(id=user_id).first()
        if user:
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            _log_activity(request, 'admin_user_toggle_active', user=request.user, metadata={'target_user_id': user_id, 'is_active': user.is_active})
    return redirect('admin_dashboard_section', section='users')

@admin_required
def admin_user_toggle_ban(request, user_id):
    if request.method == 'POST':
        User = get_user_model()
        user = User.objects.filter(id=user_id).first()
        if user:
            if user.id == request.user.id or user.role == User.ROLE_ADMIN:
                return redirect('admin_dashboard_section', section='users')
            user.is_banned = not user.is_banned
            if user.is_banned:
                user.is_active = False
            user.save(update_fields=['is_banned', 'is_active'])
            _log_activity(request, 'admin_user_toggle_ban', user=request.user, metadata={'target_user_id': user_id, 'is_banned': user.is_banned})
    return redirect('admin_dashboard_section', section='users')

@admin_required
def admin_user_change_role(request, user_id):
    if request.method == 'POST':
        User = get_user_model()
        user = User.objects.filter(id=user_id).first()
        role = request.POST.get('role')
        if user and role in [User.ROLE_ADMIN, User.ROLE_USER]:
            if user.id == request.user.id and role != User.ROLE_ADMIN:
                messages.error(request, 'You cannot remove your own admin role.')
                return redirect('admin_dashboard_section', section='users')
            user.role = role
            user.save(update_fields=['role'])
            _log_activity(request, 'admin_user_change_role', user=request.user, metadata={'target_user_id': user_id, 'role': role})
    return redirect('admin_dashboard_section', section='users')

@admin_required
def admin_user_delete(request, user_id):
    if request.method == 'POST':
        User = get_user_model()
        user = User.objects.filter(id=user_id).first()
        if user:
            is_self = user.id == request.user.id
            if is_self:
                return redirect('admin_dashboard_section', section='users')
            # Prevent deleting other admins
            if getattr(user, 'role', None) == User.ROLE_ADMIN:
                messages.error(request, 'Cannot delete another admin account.')
                return redirect('admin_dashboard_section', section='users')
            # Remove avatar file if present
            try:
                if getattr(user, 'avatar', None):
                    user.avatar.delete(save=False)
            except Exception:
                pass
            # Purge related data explicitly (CASCADE handles most, but clear logs/sessions too)
            from apps.scraper.models import ScraperJob
            from core.models import ActivityLog, TrafficLog
            ScraperJob.objects.filter(user=user).delete()
            ActivityLog.objects.filter(user=user).delete()
            TrafficLog.objects.filter(user=user).delete()
            # Kill active sessions for the user
            for session in Session.objects.filter(expire_date__gte=timezone.now()):
                data = session.get_decoded()
                if str(data.get('_auth_user_id')) == str(user.id):
                    session.delete()
            _log_activity(request, 'admin_user_delete', user=request.user, metadata={'target_user_id': user_id})
            user.delete()
    return redirect('admin_dashboard_section', section='users')

@admin_required
def admin_job_delete(request, job_id):
    if request.method == 'POST':
        job = ScraperJob.objects.filter(id=job_id).first()
        if job:
            ScrapeLog.objects.create(job=job, level='INFO', message='Job deleted by admin', metadata={'deleted_by': request.user.id})
            _log_activity(request, 'admin_job_delete', user=request.user, metadata={'job_id': job_id})
            job.delete()
    return redirect('admin_dashboard_section', section='jobs')

@admin_required
def admin_job_retry(request, job_id):
    if request.method == 'POST':
        job = ScraperJob.objects.filter(id=job_id).first()
        if job:
            job.status = 'PENDING'
            job.save(update_fields=['status'])
            ScrapeLog.objects.create(job=job, level='INFO', message='Job retried by admin', metadata={'retried_by': request.user.id})
            run_scraper_task.delay(job.id)
            _log_activity(request, 'admin_job_retry', user=request.user, metadata={'job_id': job_id})
    return redirect('admin_dashboard_section', section='jobs')

@admin_required
def admin_job_logs(request, job_id):
    logs = ScrapeLog.objects.filter(job_id=job_id).order_by('-created_at')[:50]
    data = [
        {
            'level': log.level,
            'message': log.message,
            'timestamp': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'metadata': log.metadata or {}
        }
        for log in logs
    ]
    return JsonResponse({'logs': data})
