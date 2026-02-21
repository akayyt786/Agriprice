from django.db import migrations
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os


def setup_google_oauth(apps, schema_editor):
    """Create Google SocialApp from environment variables"""
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
    google_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()
    site_domain = os.environ.get('SITE_DOMAIN', 'farmerpricealert.onrender.com').strip()
    
    if not google_client_id or not google_secret:
        print("⚠️  GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set or empty. Skipping Google OAuth setup.")
        print(f"    GOOGLE_CLIENT_ID: {'SET' if google_client_id else 'NOT SET'}")
        print(f"    GOOGLE_CLIENT_SECRET: {'SET' if google_secret else 'NOT SET'}")
        return
    
    print(f"\n🔍 DEBUG: Credentials loaded from environment:")
    print(f"   Client ID length: {len(google_client_id)}")
    print(f"   Secret length: {len(google_secret)}")
    print(f"   Site domain: {site_domain}\n")
    
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
        
        if created:
            print(f"✅ Created new Google SocialApp")
        else:
            # Update existing app with new credentials
            print(f"⚠️  Google SocialApp already exists, updating credentials")
            app.client_id = google_client_id
            app.secret = google_secret
            app.save()
        
        # Ensure Site domain and link it to the SocialApp
        from django.conf import settings as django_settings
        try:
            site, site_created = Site.objects.get_or_create(
                id=django_settings.SITE_ID,
                defaults={'domain': site_domain, 'name': 'Farmer Price Alert'}
            )
            
            if not site_created and site.domain != site_domain:
                print(f"🔧 Updating Site domain from '{site.domain}' to '{site_domain}'")
                site.domain = site_domain
                site.name = 'Farmer Price Alert'
                site.save()
            
            # Ensure app is linked to this site
            if site not in app.sites.all():
                app.sites.add(site)
                print(f"✅ Linked Google SocialApp to Site: {site.domain}")
            else:
                print(f"✅ Google SocialApp already linked to Site: {site.domain}")
                
        except Exception as e:
            print(f"❌ Error managing Site: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"✅ Google OAuth setup complete")
            
    except Exception as e:
        print(f"❌ Error setting up Google OAuth: {str(e)}")
        import traceback
        traceback.print_exc()


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
