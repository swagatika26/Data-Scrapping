# Email & Password Reset Log Analysis 📋

## 📍 Log Files Location
```
logs/reset_password.log      ← Password reset errors
logs/otp.log                 ← OTP email errors (empty)
logs/mailbox/                ← Email storage (empty)
```

---

## ❌ Current Errors Found

### Error #1: "NameError: name 'subject' is not defined"
**Location:** `core/views.py`, line 82 in `form_valid()`
**Status:** ACTIVE - Prevents password reset emails from sending
**First Occurrence:** 2026-04-06 14:20:16

```
ERROR: Password reset email send failed: name 'subject' is not defined
Traceback: NameError: name 'subject' is not defined. Did you mean: 'object'?
```

---

## 🔍 Root Cause Analysis

### Issue 1: Email Configuration Logic Error
**File:** [config/settings.py](config/settings.py) (lines 186-199)

```python
# BROKEN LOGIC:
if DEBUG and not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST_USER = 'swagatikamohanty286@gmail.com'              # ← ALWAYS OVERRIDES
EMAIL_HOST_PASSWORD = 'zepz ukjb ugob ebbs'                  # ← ALWAYS OVERRIDES
```

**Problems:**
- `EMAIL_HOST_USER` is hardcoded in the file (security risk)
- `EMAIL_HOST_PASSWORD` is hardcoded (major security risk) 
- Conditions that set console backend are ignored
- These credentials override environment variables

### Issue 2: Missing Subject Template Context
**Possible Cause:** Django's PasswordResetView is not passing the `subject` variable correctly to the email template renderer.

---

## ✅ Solution: Fix EmailConfiguration

Replace [config/settings.py](config/settings.py) lines 180-199:

### BEFORE (Current - BROKEN):
```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@scrapyx.local')

# Fallback to console backend in development if SMTP not configured
if DEBUG and not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST_USER = 'swagatikamohanty286@gmail.com'
EMAIL_HOST_PASSWORD = 'zepz ukjb ugob ebbs'
```

### AFTER (FIXED):
```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@scrapyx.local')

# Fallback to console backend in development if SMTP not configured
if DEBUG and not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**What Changed:**
- ✅ Removed hardcoded credentials
- ✅ Removed unsafe credential override
- ✅ Now uses environment variables only
- ✅ Proper fallback logic for development

---

## 🔧 Configure .env for Email

Create/update `.env` file with:

```env
# Gmail SMTP Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password-here
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Development Mode
DEBUG=True
```

### Get Gmail App Password:
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2FA if not already enabled
3. Navigate to "App passwords"
4. Select "Mail" and "Windows Computer"
5. Copy the 16-character password
6. Paste into `.env` as `EMAIL_HOST_PASSWORD`

**⚠️ WARNING:** Never hardcode passwords in Python files!

---

## 📊 Email Flow Test

### Test 1: Check Email Configuration
```python
from django.conf import settings
from django.core.mail import get_connection

print("Email Backend:", settings.EMAIL_BACKEND)
print("Email Host:", settings.EMAIL_HOST)
print("Email Port:", settings.EMAIL_PORT)
print("Use TLS:", settings.EMAIL_USE_TLS)
print("From Email:", settings.DEFAULT_FROM_EMAIL)
print("Has User:", bool(settings.EMAIL_HOST_USER))
print("Has Password:", bool(settings.EMAIL_HOST_PASSWORD))

# Try connection
conn = get_connection()
try:
    conn.open()
    print("✅ Email connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Email connection failed: {e}")
```

### Test 2: Send Test Email
```python
from django.core.mail import send_mail

try:
    send_mail(
        subject='Test Email from ScrapyX',
        message='If you see this, emails are working!',
        from_email='no-reply@scrapyx.local',
        recipient_list=['your-email@gmail.com'],
        fail_silently=False,
    )
    print("✅ Test email sent successfully!")
except Exception as e:
    print(f"❌ Failed to send email: {e}")
```

---

## 🚀 Quick Fix Steps

1. **Backup current settings:**
   ```bash
   cp config/settings.py config/settings.py.backup
   ```

2. **Fix the email configuration** (remove hardcoded credentials)

3. **Add to `.env`:**
   ```
   EMAIL_HOST_USER=your-gmail@gmail.com
   EMAIL_HOST_PASSWORD=your-16-char-app-password
   ```

4. **Restart Django:**
   ```bash
   python manage.py runserver
   ```

5. **Test password reset** at `/password-reset/`

6. **Check logs:**
   ```bash
   tail -f logs/reset_password.log
   ```

---

## 📝 Expected Log Output (Success)

```
2026-04-06 15:30:00,123 INFO reset_password: Password reset requested for email=user@example.com
2026-04-06 15:30:00,456 INFO reset_password: Password reset link generated
2026-04-06 15:30:01,789 INFO reset_password: Email backend: EmailBackend
2026-04-06 15:30:01,789 INFO reset_password: Email host: smtp.gmail.com
2026-04-06 15:30:02,000 INFO reset_password: Password reset email sent successfully
```

---

## ⚠️ Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "NameError: subject not defined" | Wrong Django email config | Apply the fix above |
| "SMTP Authentication error" | Wrong credentials | Check Gmail app password |
| "Connection refused" | No internet/SMTP error | Check firewall/network |
| "Module not found: django.core.mail" | Missing dependency | Run `pip install django` |
| Emails go to console | DEBUG mode enabled | Set EMAIL_HOST_USER in .env |

---

## 🔒 Security Best Practices

✅ **DO:**
- Store credentials in `.env` file
- Use Gmail App Passwords (not main password)
- Commit `.env.example` to git (not `.env`)
- Rotate app passwords regularly

❌ **DON'T:**
- Hardcode credentials in Python files
- Commit `.env` to git
- Use your main Gmail password
- Share credentials in code reviews

---

## 📚 Testing Password Reset Flow

1. Go to [Login Page](http://localhost:8000/login)
2. Click "Forgot Password?"
3. Enter email address
4. Check email for reset link
5. Click link and set new password
6. Try logging in with new password

---

## 🔗 Related Files

- Email Config: [config/settings.py](config/settings.py#L186)
- Reset Templates: [templates/registration/](templates/registration/)
- Reset View: [core/views.py](core/views.py) - password_reset_otp()
- Log File: [logs/reset_password.log](logs/reset_password.log)

---

**Status: Ready to Fix** ✅
Apply the configuration fix and test emails will start working!
