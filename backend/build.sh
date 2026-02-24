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
