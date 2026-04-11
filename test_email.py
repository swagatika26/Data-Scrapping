#!/usr/bin/env python
"""
Email Configuration Test Script
Run this to verify your email setup is working correctly
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from django.conf import settings
from django.core.mail import send_mail, get_connection
from django.core.mail.backends.smtp import EmailBackend

print("=" * 60)
print("EMAIL CONFIGURATION TEST")
print("=" * 60)

# Show configuration
print("\n1. CURRENT EMAIL CONFIGURATION:")
print(f"   Backend: {settings.EMAIL_BACKEND}")
print(f"   Host: {settings.EMAIL_HOST}")
print(f"   Port: {settings.EMAIL_PORT}")
print(f"   Use TLS: {settings.EMAIL_USE_TLS}")
print(f"   From Email: {settings.DEFAULT_FROM_EMAIL}")
print(f"   Debug Mode: {settings.DEBUG}")

# Check credentials
email_user = settings.EMAIL_HOST_USER
email_pass = settings.EMAIL_HOST_PASSWORD

print(f"   Email User Configured: {bool(email_user)}")
if email_user:
    print(f"   Email User: {email_user}")
else:
    print("   ❌ EMAIL_HOST_USER is EMPTY - emails will not send!")

print(f"   Email Password Configured: {bool(email_pass)}")

# Test connection
print("\n2. TESTING SMTP CONNECTION:")
try:
    conn = get_connection()
    conn.open()
    print("   ✅ Connected to SMTP server successfully!")
    conn.close()
except Exception as e:
    print(f"   ❌ Failed to connect: {e}")
    print("   Check your EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
    sys.exit(1)

# Send test email
print("\n3. SENDING TEST EMAIL:")
try:
    result = send_mail(
        subject='ScrapyX Test Email',
        message='If you receive this, your email configuration is working!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email_user],  # Send to yourself
        fail_silently=False,
    )
    print(f"   ✅ Test email sent successfully!")
    print(f"   📧 Check your email: {email_user}")
    print(f"   ⏱️  It may take 1-5 minutes to arrive")
    print(f"   💡 Check spam folder if not found in inbox")
except Exception as e:
    print(f"   ❌ Failed to send email: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nNext Steps:")
print("1. Check your email for the test message")
print("2. If you don't receive it, check your spam folder")
print("3. If still nothing, verify:")
print("   - EMAIL_HOST_USER is correct")
print("   - EMAIL_HOST_PASSWORD is correct (use Gmail App Password)")
print("   - 2FA is enabled on your Gmail account")
print("   - You've created an App Password for Gmail")
print("=" * 60)
