import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.email_utils import send_password_reset_email, send_simple_test_email
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth import get_user_model

# Test simple email first
print('=== Testing Simple Email ===')
simple_result = send_simple_test_email(
    to_email='swagatikamohanty006@gmail.com',
    subject='Test: ScrapyX Email Delivery',
    message='This is a test to verify email delivery is working properly.'
)
print(f'Simple email result: {simple_result}')

# Test password reset email
print('\n=== Testing Password Reset Email ===')
User = get_user_model()
user = User.objects.get(email='swagatikamohanty006@gmail.com')

token = default_token_generator.make_token(user)
uid = urlsafe_base64_encode(force_bytes(user.pk))
reset_link = f'http://127.0.0.1:8000/reset/{uid}/{token}/'

print(f'Reset link: {reset_link}')
reset_result = send_password_reset_email(user, reset_link)
print(f'Password reset email result: {reset_result}')

print('\n=== Email Configuration Status ===')
from django.conf import settings
print(f'Email backend: {settings.EMAIL_BACKEND}')
print(f'Email host: {settings.EMAIL_HOST}')
print(f'Email port: {settings.EMAIL_PORT}')
print(f'Email user: {settings.EMAIL_HOST_USER}')
print(f'Use TLS: {settings.EMAIL_USE_TLS}')
print(f'Email timeout: {settings.EMAIL_TIMEOUT}')
print(f'Email headers configured: {hasattr(settings, "EMAIL_HEADERS")}')
