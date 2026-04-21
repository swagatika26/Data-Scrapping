import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

print('=== Google OAuth Configuration ===')
try:
    google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
    app_config = google_config.get('APP', {})
    
    client_id = app_config.get('client_id', '')
    client_secret = app_config.get('secret', '')
    
    print(f'Google Client ID: {client_id[:20]}...' if client_id else 'Not configured')
    print(f'Google Client Secret: {"*" * len(client_secret) if client_secret else "Not configured"}')
    print(f'OAuth PKCE Enabled: {google_config.get("OAUTH_PKCE_ENABLED", False)}')
    print(f'Login Methods: {settings.ACCOUNT_LOGIN_METHODS}')
    print(f'Signup Fields: {settings.ACCOUNT_SIGNUP_FIELDS}')
    print(f'Email Verification: {settings.ACCOUNT_EMAIL_VERIFICATION}')
    print(f'Site ID: {settings.SITE_ID}')
    
    print('\n=== URL Configuration ===')
    print('Django-allauth URLs: /accounts/')
    print('Custom login: /login/')
    print('Custom signup: /signup/')
    
    print('\n=== Environment Variables ===')
    client_id_env = os.getenv("GOOGLE_CLIENT_ID", "Not set")
    client_secret_env = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    if client_id_env != "Not set":
        print(f'GOOGLE_CLIENT_ID: {client_id_env[:20]}...')
    else:
        print('GOOGLE_CLIENT_ID: Not set')
    
    if client_secret_env:
        print(f'GOOGLE_CLIENT_SECRET: {"*" * len(client_secret_env)}')
    else:
        print('GOOGLE_CLIENT_SECRET: Not set')
    
    if not client_id or not client_secret:
        print('\n⚠️  WARNING: Google OAuth credentials are not properly configured!')
    else:
        print('\n✅ Google OAuth appears to be configured')
        
except Exception as e:
    print(f'Error checking configuration: {str(e)}')
