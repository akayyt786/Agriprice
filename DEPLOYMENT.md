# Deployment Guide – Render (free plan) + Supabase PostgreSQL

> **No terminal access needed.** Everything runs automatically via `build.sh`
> on every deploy. Just set the environment variables below once.

---

## What happens automatically on every deploy

`build.sh` runs these steps in order:

1. `pip install -r requirements.txt` – installs all Python packages
2. `python manage.py collectstatic` – bundles CSS/JS
3. `python manage.py migrate` – creates / updates database tables
4. `python manage.py setup_social_apps` – registers Google OAuth in the DB
5. `python manage.py create_superuser_from_env` – creates the Django admin account

---

## Step-by-step: one-time setup

### Step 1 – Get your Supabase DATABASE_URL

1. Go to [supabase.com](https://supabase.com) → create a new project
2. Go to **Project Settings** → **Database**
3. Scroll to **Connection string** → click **URI** → copy the URL (looks like):
   ```
   postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres
   ```
4. Keep this handy – you'll paste it into Render in Step 3.

---

### Step 2 – Generate a SECRET_KEY

Run this in any Python environment (or use an online tool):
```
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
Example output: `3xKj9p2mNqRtWzLv8yHcBdFeGsAoUiYk7nP4QwXm6rVjT1CbEI5`

---

### Step 3 – Set environment variables in Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Open your **Web Service** → click **Environment** (left sidebar)
3. Click **Add Environment Variable** and add **every row** in the table below:

| Variable | Value |
|---|---|
| `DEBUG` | `False` |
| `SECRET_KEY` | *(paste the key from Step 2)* |
| `DATABASE_URL` | *(paste the Supabase URL from Step 1)* |
| `SITE_DOMAIN` | `farmerpricealert.onrender.com` |
| `DJANGO_SUPERUSER_EMAIL` | your admin email, e.g. `admin@example.com` |
| `DJANGO_SUPERUSER_USERNAME` | your admin username, e.g. `admin` |
| `DJANGO_SUPERUSER_PASSWORD` | a strong password for Django admin |
| `GOOGLE_CLIENT_ID` | from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | from Google Cloud Console |
| `CLOUDINARY_CLOUD_NAME` | from cloudinary.com dashboard |
| `CLOUDINARY_API_KEY` | from cloudinary.com dashboard |
| `CLOUDINARY_API_SECRET` | from cloudinary.com dashboard |
| `EMAIL_HOST_USER` | your Gmail address |
| `EMAIL_HOST_PASSWORD` | your Gmail **App Password** (16-char, no spaces) |
| `GOV_API_KEY` | from data.gov.in |
| `FRONTEND_URL` | URL of your frontend (optional, for CORS) |

4. Click **Save Changes**

---

### Step 4 – Set Render build & start commands

In your Render service → **Settings**:

| Setting | Value |
|---|---|
| **Root Directory** | `backend` |
| **Build Command** | `./build.sh` |
| **Start Command** | `gunicorn backend.wsgi:application` |

---

### Step 5 – Deploy

Click **Manual Deploy → Deploy latest commit**.

Watch the build logs. A successful deploy ends with lines like:
```
Superuser 'admin' created.
==> Your service is live 🎉
```

---

### Step 6 – Access Django admin

Open `https://farmerpricealert.onrender.com/admin/` and log in with the
`DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` you set above.

---

## Re-deploys

Every `git push` to your connected branch triggers a new Render build.
`build.sh` is fully idempotent – it's safe to run multiple times.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `KeyError: 'collectstatic'` | `SECRET_KEY` env var is missing – add it in Render environment |
| `OperationalError: could not connect to server` | `DATABASE_URL` is wrong or Supabase project is paused – check the Supabase dashboard |
| Admin login fails | `DJANGO_SUPERUSER_PASSWORD` env var was not set before the first deploy – update it and **re-deploy** |
| Google login shows "third-party error" | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` missing, or the callback URL `https://farmerpricealert.onrender.com/accounts/google/login/callback/` is not added to Google Cloud Console's **Authorised redirect URIs** |
| Emails not sending | Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`; make sure you used a Gmail **App Password**, not your login password |
