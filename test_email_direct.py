import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

print('Testing direct SMTP connection...')
print(f'SMTP Host: {settings.EMAIL_HOST}')
print(f'SMTP Port: {settings.EMAIL_PORT}')
print(f'SMTP User: {settings.EMAIL_HOST_USER}')

try:
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Test Password Reset - ScrapyX'
    msg['From'] = settings.DEFAULT_FROM_EMAIL
    msg['To'] = 'swagatikamohanty006@gmail.com'
    
    # HTML body
    html = '''
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #333; text-align: center;">Password Reset Request</h2>
            <p style="color: #666; font-size: 16px;">Hello swagatikamohanty006@gmail.com,</p>
            <p style="color: #666; font-size: 16px;">You requested a password reset for your ScrapyX account.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://127.0.0.1:8000/reset/NA/d7c9uw-22914a2c18df032d79ef02fb8455f7b2/" 
                   style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                   Reset Password
                </a>
            </div>
            <p style="color: #999; font-size: 14px; text-align: center;">If the button doesn't work, copy and paste this link:</p>
            <p style="color: #999; font-size: 12px; text-align: center; word-break: break-all;">http://127.0.0.1:8000/reset/NA/d7c9uw-22914a2c18df032d79ef02fb8455f7b2/</p>
            <p style="color: #999; font-size: 14px; text-align: center; margin-top: 30px;">If you didn't request this, please ignore this email.</p>
        </div>
    </body>
    </html>
    '''
    
    msg.attach(MIMEText(html, 'html'))
    
    # Send via SMTP
    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    server.starttls()
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.send_message(msg)
    server.quit()
    
    print('Email sent successfully via direct SMTP!')
    print('Check swagatikamohanty006@gmail.com for the reset email.')
    
except Exception as e:
    print(f'SMTP Error: {str(e)}')
    import traceback
    traceback.print_exc()
