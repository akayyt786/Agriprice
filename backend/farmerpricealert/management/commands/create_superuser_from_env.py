"""
Creates (or updates) a Django superuser from environment variables.

Required environment variables:
    DJANGO_SUPERUSER_EMAIL     – superuser email address
    DJANGO_SUPERUSER_USERNAME  – superuser username
    DJANGO_SUPERUSER_PASSWORD  – superuser password (use a strong password;
                                  keep it secret in your deployment platform's
                                  environment variable settings)

This command is idempotent: if the user already exists it updates the
password and ensures is_superuser / is_staff flags are set.  It is called
from build.sh so it runs automatically on every Render deploy without
needing terminal access.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update a superuser from DJANGO_SUPERUSER_* environment variables."

    def handle(self, *args, **options):
        User = get_user_model()

        email = (os.environ.get("DJANGO_SUPERUSER_EMAIL") or "").strip()
        username = (os.environ.get("DJANGO_SUPERUSER_USERNAME") or "").strip()
        password = (os.environ.get("DJANGO_SUPERUSER_PASSWORD") or "").strip()

        if not email or not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Skipping superuser creation: "
                    "DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_USERNAME, and "
                    "DJANGO_SUPERUSER_PASSWORD must all be set."
                )
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        # Always apply latest password and flags (idempotent updates)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' already exists – updated."))
