#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Setup social apps (Google OAuth) and fix Site domain
python manage.py setup_social_apps

# Create / update the Django admin superuser from env vars (no terminal needed)
# Requires: DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD
python manage.py create_superuser_from_env

# Sync today's mandi prices from Gov API into the database
# This ensures fresh data is available immediately after deploy
# Non-fatal: if this fails, the /api/sync-daily/ endpoint will handle it later
echo "📡 Syncing today's mandi prices..."
set +e  # Temporarily allow errors (don't fail build if sync fails)
if command -v curl &> /dev/null; then
    python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
from farmerpricealert.views import _sync_all_mandi_prices
_sync_all_mandi_prices()
" && echo "✅ Mandi sync complete!" || echo "⚠️ Mandi sync failed (non-fatal), will retry via /api/sync-daily/"
else
    echo "⚠️ curl not found, skipping build-time sync. Will sync via /api/sync-daily/ at runtime."
fi
set -e  # Re-enable strict error handling
