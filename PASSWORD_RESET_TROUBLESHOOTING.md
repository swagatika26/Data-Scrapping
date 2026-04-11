# Password Reset Email Troubleshooting Guide

## ✅ Status Check
- **Email System:** Working ✅
- **SMTP Connection:** Connected to smtp.gmail.com:587 ✅  
- **Test Email Sent:** Successfully sent to pritiballarisahoo@gmail.com ✅
- **From Address:** swagatikamohanty286@gmail.com ✅

---

## 🔍 Troubleshooting Steps

### Step 1: Check Your Email
1. Go to **pritiballarisahoo@gmail.com**
2. Check these folders in order:
   - ✅ **Inbox** - Most likely location
   - 📬 **Spam/Promotions** - Gmail often filters password reset emails here
   - 📋 **All Mail** - Check if it arrived at all
   - 🗑️ **Trash** - In case it was accidentally deleted

3. **Search for:** "ScrapyX" or "password reset"

### Step 2: Check Gmail Settings
If emails are not arriving at all:

1. **Login to pritiballarisahoo@gmail.com**
2. Go to **Settings** (gear icon)
3. Click **Forwarding and POP/IMAP**
4. Ensure IMAP is **Enabled**
5. Go to **Security** tab
6. Check **App passwords** or **Less secure app access**

### Step 3: Check Spam Filters
Gmail might be filtering emails. To add to safe senders:

1. Check your **Spam folder**
2. Find email from: `swagatikamohanty286@gmail.com`
3. Click **"Report not spam"** or **"Add to contacts"**

### Step 4: Request Password Reset Again
1. Go to password reset page: `http://localhost:8000/password-reset/otp/`
2. Enter email: `pritiballarisahoo@gmail.com`
3. Click **Send Reset Code**
4. **Wait 2-5 minutes** for email to arrive
5. Check email again (Inbox + Spam)

---

## 📧 What Email You Should See

**From:** swagatikamohanty286@gmail.com  
**Subject:** ScrapyX password reset code  
**Content:** Your OTP is XXXXXX. It expires in 10 minutes.

---

## 🔐 Password Reset Process

### Full Flow:
1. Go to: `http://localhost:8000/password-reset/otp/`
2. Enter: `pritiballarisahoo@gmail.com`
3. Click: **"Send Reset Code"**
4. **Wait for email** with OTP code
5. Enter OTP code on the page
6. Create new password
7. Login with new password

---

## ⚠️ Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Email not in inbox | Gmail spam filter | Check Spam/Promotions folder |
| Email says "SPAM" | From different domain | Add to contacts in Gmail |
| "OTP expired" | Took too long to verify | Request new OTP (Resend button) |
| "Invalid OTP" | Typed code wrong | Copy-paste instead of typing |
| "Email not found" | Email not registered | Sign up first, then reset password |
| Can't click reset link | JavaScript issue | Refresh page and try again |

---

## 🧪 Test Email Verification

**Last test sent:**
```
✅ EMAIL SENT SUCCESSFULLY!
From: swagatikamohanty286@gmail.com
To: pritiballarisahoo@gmail.com
Subject: ScrapyX Password Reset Test
```

If you received this test email, your email system is working correctly.

---

## 📋 Quick Checklist

- [ ] Checked email **Inbox**
- [ ] Checked email **Spam/Promotions** folders
- [ ] Enabled **IMAP** in Gmail settings
- [ ] Added sender to **Contacts**
- [ ] Waited **2-5 minutes** for email to arrive
- [ ] Tried **requesting reset again**
- [ ] Checked **All Mail** folder
- [ ] Received the **test email** above

---

## 🚀 Next Steps

1. **If you received test email:**
   - Go to `http://localhost:8000/password-reset/otp/`
   - Enter `pritiballarisahoo@gmail.com`
   - You should receive password reset email

2. **If you didn't receive test email:**
   - Check your spam/promotions folder
   - Add `swagatikamohanty286@gmail.com` to your contacts
   - Ask your email admin to whitelist the sender

---

## 📞 Technical Details

**Configuration:**
- Email Backend: SMTP (smtp.gmail.com:587)
- TLS Enabled: Yes
- From Address: swagatikamohanty286@gmail.com
- Test Status: ✅ Working

**Recent Successful Sends:**
- 2026-04-07 11:45:39 - Email sent successfully
- 2026-04-06 16:18:14 - Email sent successfully
- 2026-04-06 14:28:17 - Email sent successfully

---

## 💡 Pro Tips

1. **Whitelist the sender:** Add `swagatikamohanty286@gmail.com` to your Gmail contacts for future password resets
2. **Check different browser:** Try another browser if it's a JavaScript issue
3. **Clear browser cache:** Press `Ctrl+Shift+Delete` and clear all
4. **Try incognito mode:** Some browser extensions might block password reset
5. **Different device:** Try password reset on your phone if desktop isn't working

---

**Status: Email System is WORKING ✅**

If you're still not receiving emails after checking all items above, there may be a Gmail-specific issue. Try these final steps:

1. Check: https://myaccount.google.com/notifications
2. Check: https://myaccount.google.com/security-checkup
3. Forward inbox: Settings → Forwarding to another email
4. Contact Gmail Support: https://support.google.com
