#!/usr/bin/env python
"""
Complete test of password reset email system with logging
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

# Get the logger for password reset
logger = logging.getLogger('reset_password')

print("=" * 70)
print("PASSWORD RESET EMAIL SYSTEM - COMPLETE TEST")
print("=" * 70)

# Step 1: Check logging setup
print("\n1. CHECKING LOGGING SETUP:")
print(f"   Logger name: reset_password")
print(f"   Logger level: {logger.level}")
print(f"   Handlers: {[h.__class__.__name__ for h in logger.handlers]}")
print(f"   Log file: logs/reset_password.log")

# Step 2: Send test email to existing user
User = get_user_model()
test_email = 'swagatikamohanty006@gmail.com'
user = User.objects.filter(email__iexact=test_email).first()

if user:
    print(f"\n2. FOUND TEST USER: {user.email}")
    
    # Log password reset request
    logger.info(f"Password reset requested for email={user.email}")
    print(f"   ✅ Logged: Password reset request")
    
    # Generate token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = f'http://localhost:8000/reset/{uid}/{token}/'
    
    logger.info(f"Password reset link generated for email={user.email}: {reset_url}")
    print(f"   ✅ Logged: Reset link generated")
    
    # Log email config
    logger.info(f"Email backend: {settings.EMAIL_BACKEND.split('.')[-1]}")
    logger.info(f"Email host: {settings.EMAIL_HOST}")
    logger.info(f"Email port: {settings.EMAIL_PORT}")
    logger.info(f"Email use TLS: {settings.EMAIL_USE_TLS}")
    logger.info(f"Email user: {settings.EMAIL_HOST_USER}")
    print(f"   ✅ Logged: Email configuration")
    
    # Send email
    print(f"\n3. SENDING TEST EMAIL:")
    try:
        send_mail(
            subject='ScrapyX Password Reset Code',
            message=f'Click here to reset your password: {reset_url}\n\nThis link expires in 24 hours.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Password reset email sent successfully to {user.email}")
        print(f"   ✅ EMAIL SENT SUCCESSFULLY!")
        print(f"   To: {user.email}")
        print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
    except Exception as e:
        logger.error(f"Password reset email send failed: {e}")
        logger.exception("Password reset email exception")
        print(f"   ❌ EMAIL FAILED: {e}")

else:
    print(f"   ❌ User not found: {test_email}")

print(f"\n4. LOG FILE STATUS:")
log_file = 'logs/reset_password.log'
import os
if os.path.exists(log_file):
    file_size = os.path.getsize(log_file)
    print(f"   ✅ Log file exists: {log_file}")
    print(f"   Size: {file_size} bytes")
    print(f"\n   Last 5 lines of log:")
    with open(log_file, 'r') as f:
        lines = f.readlines()
        for line in lines[-5:]:
            print(f"   {line.rstrip()}")
else:
    print(f"   ❌ Log file not found")

print("\n" + "=" * 70)
print("TEST COMPLETE - Check logs/reset_password.log for details")
print("=" * 70)
