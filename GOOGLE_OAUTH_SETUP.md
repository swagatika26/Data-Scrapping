# Google OAuth Setup Guide for ScrapyX

## 🚀 Quick Setup Guide

### Step 1: Get Google OAuth Credentials

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Select or create a project**
3. **Enable APIs**:
   - Go to "APIs & Services" → "Library"
   - Search and enable "Google+ API" and "Google People API"
4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Select "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8000/accounts/google/login/callback/`
     - `http://127.0.0.1:8000/accounts/google/login/callback/`
     - `https://yourdomain.com/accounts/google/login/callback/` (for production)
5. **Copy your Client ID and Client Secret**

### Step 2: Update Environment Variables

Add these to your `.env` file:

```bash
# Google OAuth Credentials
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id_here
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret_here
```

### Step 3: Test the Setup

1. **Restart your Django server**:
   ```bash
   python manage.py runserver
   ```

2. **Visit the login page**: http://localhost:8000/login/

3. **Click "Log in with Google"**

4. **Complete the OAuth flow** in Google

5. **You should be redirected back** to your dashboard

## 🔧 Configuration Details

### What's Already Configured:

✅ **django-allauth** installed and configured  
✅ **Authentication backends** set up  
✅ **URLs** configured at `/accounts/`  
✅ **Templates** updated with OAuth links  
✅ **Database migrations** applied  

### Environment Variables Required:

```bash
GOOGLE_OAUTH2_CLIENT_ID=your_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_client_secret
```

### Key URLs:

- **Login**: `/accounts/login/`
- **Signup**: `/accounts/signup/`
- **Google OAuth**: `/accounts/google/login/`
- **Google Callback**: `/accounts/google/login/callback/`
- **Logout**: `/accounts/logout/`

## 🛠️ Troubleshooting

### Common Issues:

1. **"redirect_uri_mismatch" Error**:
   - Check that your redirect URI matches exactly in Google Console
   - Include trailing slash: `http://localhost:8000/accounts/google/login/callback/`

2. **"invalid_client" Error**:
   - Verify your Client ID and Secret are correct
   - Make sure environment variables are loaded

3. **"access_denied" Error**:
   - Check that OAuth consent screen is configured
   - Verify application is not in testing mode (or add test users)

4. **Template Error**:
   - Ensure `{% load socialaccount %}` is in your template
   - Check that allauth context processors are configured

### Debug Mode:

Add to settings for debugging:
```python
DEBUG = True
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Disable email verification for testing
```

## 📋 Production Checklist

- [ ] Use HTTPS URLs in production
- [ ] Add production domain to authorized redirect URIs
- [ ] Enable email verification
- [ ] Configure proper domain in Django sites
- [ ] Set up proper CSP headers if needed
- [ ] Monitor OAuth usage in Google Console

## 🎯 Next Steps

Once Google Sign-In is working:

1. **Customize redirect behavior** in settings
2. **Add user profile synchronization**
3. **Implement role-based access**
4. **Add social account linking in user settings**
5. **Set up analytics for OAuth usage**

## 📞 Support

If you encounter issues:

1. Check Django logs: `python manage.py runserver --verbosity=2`
2. Verify environment variables: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GOOGLE_OAUTH2_CLIENT_ID'))"`
3. Check Google Console for API errors
4. Review allauth documentation: https://docs.allauth.org/en/latest/
