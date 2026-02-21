from django.db import migrations
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os


def setup_google_oauth(apps, schema_editor):
    """Create Google SocialApp from environment variables"""
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    google_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    if not google_client_id or not google_secret:
        print("⚠️  GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set. Skipping Google OAuth setup.")
        return
    
    try:
        # Get or create the Google SocialApp
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': google_client_id,
                'secret': google_secret,
            }
        )
        
        # Add current site to the app
        try:
            site = Site.objects.get_current()
            if site not in app.sites.all():
                app.sites.add(site)
        except Exception as e:
            print(f"⚠️  Could not add site to Google SocialApp: {str(e)}")
        
        if created:
            print("✅ Successfully created Google SocialApp from environment variables")
        else:
            # Update existing app with new credentials
            app.client_id = google_client_id
            app.secret = google_secret
            app.save()
            print("✅ Successfully updated Google SocialApp with new credentials")
            
    except Exception as e:
        print(f"❌ Error setting up Google OAuth: {str(e)}")


def reverse_setup(apps, schema_editor):
    """Remove Google SocialApp on rollback"""
    try:
        SocialApp.objects.filter(provider='google').delete()
        print("✅ Removed Google SocialApp")
    except Exception as e:
        print(f"⚠️  Could not remove Google SocialApp: {str(e)}")


class Migration(migrations.Migration):

    dependencies = [
        ('farmerpricealert', '0007_alter_user_email'),
    ]

    operations = [
        migrations.RunPython(setup_google_oauth, reverse_setup),
    ]
