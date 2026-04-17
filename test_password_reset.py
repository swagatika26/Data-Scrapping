#!/usr/bin/env python
"""
Test password reset email system
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger('reset_password')

User = get_user_model()

# Find user with that email
user = User.objects.filter(email__iexact='pritiballarisahoo@gmail.com').first()

if user:
    print("=" * 60)
    print("PASSWORD RESET TEST")
    print("=" * 60)
    
    logger.info(f'Password reset requested for email={user.email}')
    print(f'✅ Logged: Password reset requested for {user.email}')
    
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = f'http://localhost:8000/reset/{uid}/{token}/'
    
    logger.info(f'Password reset link generated: {reset_url}')
    print(f'✅ Logged: Password reset link generated')
    
    logger.info(f'Email backend: {settings.EMAIL_BACKEND.split(".")[-1]}')
    logger.info(f'Email host: {settings.EMAIL_HOST}')
    logger.info(f'Email port: {settings.EMAIL_PORT}')
    logger.info(f'Email use TLS: {settings.EMAIL_USE_TLS}')
    logger.info(f'Email user: {settings.EMAIL_HOST_USER}') 
    print(f'✅ Logged: Email configuration')
    
    try:
        send_mail(
            subject='Password reset for ScrapyX',
            message=f'Click here to reset: {reset_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f'Password reset email sent successfully to {user.email}')
        print(f'✅ TEST EMAIL SENT TO {user.email}!')
    except Exception as e:
        logger.error(f'Email send failed: {e}')
        print(f'❌ EMAIL FAILED: {e}')
    
    print("=" * 60)
    print("Check logs/reset_password.log for details")
    print("=" * 60)
else:
    print('❌ User not found with email pritiballarisahoo@gmail.com')
