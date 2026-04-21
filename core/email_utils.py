"""
Custom email utilities for better Gmail deliverability
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string


def send_password_reset_email(user, reset_link):
    """
    Send password reset email with proper headers and formatting
    to avoid Gmail spam filters
    """
    subject = '[ScrapyX] Password Reset Request'
    
    # Plain text version
    text_content = f'''
Hello {user.username},

You requested a password reset for your ScrapyX account.

Click the link below to reset your password:
{reset_link}

If you cannot click the link, copy and paste it into your browser.

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Thank you,
ScrapyX Team
    '''.strip()
    
    # Simple HTML version to avoid template issues
    html_content = f'''
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h2 style="color: #333; text-align: center;">Password Reset Request</h2>
        <p style="color: #666; font-size: 16px;">Hello {user.username},</p>
        <p style="color: #666; font-size: 16px;">You requested a password reset for your ScrapyX account.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" 
               style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
               Reset Password
            </a>
        </div>
        <p style="color: #999; font-size: 14px; text-align: center;">If the button doesn't work, copy and paste this link:</p>
        <p style="color: #999; font-size: 12px; text-align: center; word-break: break-all;">{reset_link}</p>
        <p style="color: #999; font-size: 14px; text-align: center; margin-top: 30px;">If you didn't request this, please ignore this email.</p>
    </div>
</body>
</html>
    '''
    
    # Create email with custom headers
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
        headers={
            'X-Priority': '3',
            'X-Mailer': 'ScrapyX Password Reset',
            'Reply-To': settings.EMAIL_HOST_USER,
            'List-Unsubscribe': f'<mailto:{settings.EMAIL_HOST_USER}?subject=unsubscribe>',
        }
    )
    
    email.attach_alternative(html_content, 'text/html')
    
    try:
        result = email.send()
        return result > 0
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False


def send_simple_test_email(to_email, subject, message):
    """
    Send a simple test email for debugging
    """
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
            headers={
                'X-Priority': '3',
                'X-Mailer': 'ScrapyX Test',
            }
        )
        result = email.send()
        return result > 0
    except Exception as e:
        print(f"Test email failed: {str(e)}")
        return False
