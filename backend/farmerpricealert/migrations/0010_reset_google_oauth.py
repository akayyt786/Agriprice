from django.db import migrations
import os


def reset_google_oauth_credentials(apps, schema_editor):
    """Reset Google OAuth credentials from environment - handles whitespace issues"""
    from allauth.socialaccount.models import SocialApp
    from django.contrib.sites.models import Site
    from django.conf import settings
    
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
    google_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()
    site_domain = os.environ.get('SITE_DOMAIN', 'farmerpricealert.onrender.com').strip()
    
    print("\n" + "=" * 80)
    print("RESETTING GOOGLE OAUTH CREDENTIALS")
    print("=" * 80)
    
    if not google_client_id or not google_secret:
        print("❌ ERROR: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set or empty!")
        print(f"   GOOGLE_CLIENT_ID present: {bool(os.environ.get('GOOGLE_CLIENT_ID'))}")
        print(f"   GOOGLE_CLIENT_SECRET present: {bool(os.environ.get('GOOGLE_CLIENT_SECRET'))}")
        print("\nPlease set these environment variables in Render and push again.")
        return
    
    print(f"✅ Credentials found in environment:")
    print(f"   Client ID: {google_client_id[:20]}... (length: {len(google_client_id)})")
    print(f"   Secret: {google_secret[:20]}... (length: {len(google_secret)})")
    print(f"   Site Domain: {site_domain}\n")
    
    try:
        # Get or create Site first
        site, site_created = Site.objects.get_or_create(
            id=settings.SITE_ID,
            defaults={'domain': site_domain, 'name': 'Farmer Price Alert'}
        )
        
        if site_created:
            print(f"✅ Created new Site: {site.domain}")
        elif site.domain != site_domain:
            print(f"🔧 Updating Site domain: {site.domain} → {site_domain}")
            site.domain = site_domain
            site.save()
        else:
            print(f"✅ Site already configured: {site.domain}")
        
        # Delete old app if it exists  
        old_app = SocialApp.objects.filter(provider='google').first()
        if old_app:
            print(f"\n🔧 Found existing Google SocialApp, checking for credential mismatch...")
            print(f"   Stored Client ID: {old_app.client_id[:20]}...")
            print(f"   Stored Secret: {old_app.secret[:20]}...")
            
            client_id_match = old_app.client_id == google_client_id
            secret_match = old_app.secret == google_secret
            
            if not client_id_match or not secret_match:
                print(f"\n❌ CREDENTIALS MISMATCH DETECTED!")
                print(f"   Client ID matches: {client_id_match}")
                print(f"   Secret matches: {secret_match}")
                print(f"\n🗑️  Deleting old SocialApp to recreate with correct credentials...")
                old_app.delete()
            else:
                print(f"✅ Credentials match, no update needed")
                # Still ensure site is linked
                if site not in old_app.sites.all():
                    old_app.sites.add(site)
                    print(f"✅ Linked SocialApp to Site")
                return
        
        # Create/recreate the SocialApp with correct credentials
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': google_client_id,
                'secret': google_secret,
            }
        )
        
        # Ensure site is linked
        if site not in app.sites.all():
            app.sites.add(site)
        
        print(f"\n{'✅ Created' if created else '✅ Updated'} Google SocialApp with credentials from environment")
        print(f"   Client ID: {app.client_id[:20]}... (length: {len(app.client_id)})")
        print(f"   Secret: {app.secret[:20]}... (length: {len(app.secret)})")
        print(f"   Linked to Site: {site.domain}")
        
        print("\n" + "=" * 80)
        print("✅ GOOGLE OAUTH CREDENTIALS RESET COMPLETE")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def reverse_reset(apps, schema_editor):
    """No reverse needed - previous migration can handle it"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('farmerpricealert', '0009_fix_site_domain'),
    ]

    operations = [
        migrations.RunPython(reset_google_oauth_credentials, reverse_reset),
    ]
