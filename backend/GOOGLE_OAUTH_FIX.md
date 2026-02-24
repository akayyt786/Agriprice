# Google OAuth Login Fix Guide

## Problem
Getting "Third-Party Login Failure" when trying to login with Google because OAuth credentials are not configured.

## Root Cause
- ❌ `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` environment variables are not set
- ❌ No Google SocialApp exists in the database
- ❌ Django AllAuth cannot complete OAuth callback without these credentials

## Solution Steps

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select your project
3. Navigate to: **APIs & Services → Credentials**
4. Click **"+ CREATE CREDENTIALS"** → **"OAuth 2.0 Client ID"**
5. Application type: **Web application**
6. Add **Authorized redirect URIs**:
   ```
   https://farmerpricealert.onrender.com/accounts/google/login/callback/
   http://127.0.0.1:8000/accounts/google/login/callback/
   ```
7. Click **CREATE**
8. Copy your **Client ID** and **Client Secret**

### 2. Configure Local Environment

Edit `backend/.env` file and replace the placeholder values:

```env
GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret
SITE_DOMAIN=farmerpricealert.onrender.com
```

### 3. Set Up Google OAuth Locally

Run the setup command:

```bash
cd backend
python manage.py setup_google_oauth
```

You should see:
```
✅ GOOGLE OAUTH SETUP COMPLETE
```

### 4. Configure Production (Render)

1. Go to your Render dashboard
2. Select your web service
3. Navigate to **Environment** tab
4. Add these environment variables:
   - `GOOGLE_CLIENT_ID` = (your client ID)
   - `GOOGLE_CLIENT_SECRET` = (your client secret)
   - `SITE_DOMAIN` = `farmerpricealert.onrender.com`
5. Click **Save Changes**
6. Render will automatically redeploy

The migration `0010_reset_google_oauth.py` will automatically configure OAuth on deployment.

### 5. Test the Login

**Local:**
```bash
python manage.py runserver
```
Visit: http://127.0.0.1:8000/login/

**Production:**
Visit: https://farmerpricealert.onrender.com/login/

Click "Sign in with Google" - it should now work! ✅

## Troubleshooting

### Still getting errors after setup?

Check if credentials are loaded:
```bash
python manage.py shell -c "from allauth.socialaccount.models import SocialApp; print(SocialApp.objects.filter(provider='google').exists())"
```

Should return: `True`

### Verify Site configuration:
```bash
python manage.py shell -c "from django.contrib.sites.models import Site; print(Site.objects.get(id=2).domain)"
```

Should return: `farmerpricealert.onrender.com`

### Re-run setup if needed:
```bash
python manage.py setup_google_oauth
```

## Important Notes

- ⚠️ Keep your Client Secret private - never commit it to Git
- 🔒 `.env` file is in `.gitignore` - don't remove it
- 🌐 Make sure redirect URIs in Google Console exactly match your application URLs
- 📝 After changing Render environment variables, the app redeploys automatically

## Alternative: Manual Setup via Admin Panel

If you prefer, you can also configure OAuth through Django Admin:

1. Go to http://127.0.0.1:8000/admin/ (or your production URL)
2. Login with superuser account
3. Navigate to **Sites → Sites**
   - Verify site ID 2 has domain: `farmerpricealert.onrender.com`
4. Navigate to **Social Accounts → Social applications**
5. Click **Add Social Application**
   - Provider: Google
   - Name: Google
   - Client ID: (paste your client ID)
   - Secret key: (paste your secret)
   - Sites: Select your site (farmerpricealert.onrender.com)
6. Save

## Success Indicators

When correctly configured, you'll see in the migration output:
```
✅ Created Google SocialApp with credentials from environment
✅ Linked to Site: farmerpricealert.onrender.com
```

And users can successfully login with Google! 🎉
