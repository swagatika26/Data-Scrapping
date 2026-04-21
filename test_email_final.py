import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

# Get the user
User = get_user_model()
user = User.objects.get(email='swagatikamohanty006@gmail.com')

# Generate fresh token
token = default_token_generator.make_token(user)
uid = urlsafe_base64_encode(force_bytes(user.pk))
reset_link = f'http://127.0.0.1:8000/reset/{uid}/{token}/'

print('=== Testing with Different Subject and Content ===')
print(f'Reset link: {reset_link}')

# Try with different subject and simpler content
try:
    result = send_mail(
        subject='URGENT: Password Reset Required',
        message=f'''
SCRAPYX PASSWORD RESET

You requested to reset your password.

Reset Link: {reset_link}

Click the link above to reset your password.
This link expires in 1 hour.

If you didn't request this, ignore this email.
        ''',
        from_email='noreply@scrapyx.app',  # Try different from address
        recipient_list=['swagatikamohanty006@gmail.com'],
        fail_silently=False,
    )
    print(f'Email with different from address sent! Result: {result}')
    
except Exception as e:
    print(f'Error with different from address: {str(e)}')
    
    # Fallback to original
    try:
        result = send_mail(
            subject='Password Reset - ScrapyX',
            message=f'Please reset your password: {reset_link}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['swagatikamohanty006@gmail.com'],
            fail_silently=False,
        )
        print(f'Fallback email sent! Result: {result}')
    except Exception as e2:
        print(f'Fallback also failed: {str(e2)}')

print('\n=== Gmail Security Suggestions ===')
print('If you are not receiving emails:')
print('1. Check your Gmail spam folder')
print('2. Check Gmail Promotions/Social tabs')
print('3. Make sure Gmail is not blocking emails from swagatikamohanty286@gmail.com')
print('4. The sender Gmail account may need "Allow less secure apps" enabled')
print('5. Check if Gmail has any delivery restrictions in place')
