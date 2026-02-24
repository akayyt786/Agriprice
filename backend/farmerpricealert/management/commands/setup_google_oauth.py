"""
Management command to manually set up Google OAuth credentials
Usage: python manage.py setup_google_oauth
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
from allauth.socialaccount.models import SocialApp
import os


class Command(BaseCommand):
    help = 'Set up Google OAuth credentials from environment variables'

    def handle(self, *args, **options):
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
        google_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()
        site_domain = os.environ.get('SITE_DOMAIN', 'farmerpricealert.onrender.com').strip()
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.WARNING("GOOGLE OAUTH SETUP"))
        self.stdout.write("=" * 80 + "\n")
        
        # Validate credentials
        if not google_client_id or not google_secret:
            self.stdout.write(self.style.ERROR("❌ ERROR: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set!"))
            self.stdout.write(f"   GOOGLE_CLIENT_ID present: {bool(google_client_id)}")
            self.stdout.write(f"   GOOGLE_CLIENT_SECRET present: {bool(google_secret)}")
            self.stdout.write("\n" + self.style.WARNING("Please set these environment variables and try again:"))
            self.stdout.write("   1. Edit backend/.env file")
            self.stdout.write("   2. Replace placeholder values with actual Google OAuth credentials")
            self.stdout.write("   3. Run this command again\n")
            return
        
        # Check for placeholder values
        if 'your-client-id' in google_client_id or 'your-client-secret' in google_secret:
            self.stdout.write(self.style.ERROR("❌ ERROR: Placeholder values detected!"))
            self.stdout.write("   Please replace with actual credentials from Google Cloud Console\n")
            return
        
        self.stdout.write(self.style.SUCCESS("✅ Credentials found in environment:"))
        self.stdout.write(f"   Client ID: {google_client_id[:20]}... (length: {len(google_client_id)})")
        self.stdout.write(f"   Secret: {google_secret[:20]}... (length: {len(google_secret)})")
        self.stdout.write(f"   Site Domain: {site_domain}\n")
        
        try:
            # Get or create Site
            site, site_created = Site.objects.get_or_create(
                id=settings.SITE_ID,
                defaults={'domain': site_domain, 'name': 'Farmer Price Alert'}
            )
            
            if site_created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created new Site: {site.domain}"))
            elif site.domain != site_domain:
                self.stdout.write(self.style.WARNING(f"🔧 Updating Site domain: {site.domain} → {site_domain}"))
                site.domain = site_domain
                site.save()
            else:
                self.stdout.write(self.style.SUCCESS(f"✅ Site already configured: {site.domain}"))
            
            # Delete old app if credentials don't match
            old_app = SocialApp.objects.filter(provider='google').first()
            if old_app:
                self.stdout.write("\n🔧 Found existing Google SocialApp...")
                
                client_id_match = old_app.client_id == google_client_id
                secret_match = old_app.secret == google_secret
                
                if not client_id_match or not secret_match:
                    self.stdout.write(self.style.WARNING("❌ Credentials mismatch - deleting old app..."))
                    old_app.delete()
                else:
                    self.stdout.write(self.style.SUCCESS("✅ Credentials match!"))
                    if site not in old_app.sites.all():
                        old_app.sites.add(site)
                        self.stdout.write(self.style.SUCCESS("✅ Linked SocialApp to Site"))
                    self.stdout.write("\n" + "=" * 80)
                    self.stdout.write(self.style.SUCCESS("✅ GOOGLE OAUTH IS ALREADY CONFIGURED"))
                    self.stdout.write("=" * 80 + "\n")
                    return
            
            # Create/recreate the SocialApp
            app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': google_client_id,
                    'secret': google_secret,
                }
            )
            
            # Update if not created (shouldn't happen, but just in case)
            if not created:
                app.client_id = google_client_id
                app.secret = google_secret
                app.save()
            
            # Ensure site is linked
            if site not in app.sites.all():
                app.sites.add(site)
            
            self.stdout.write("\n" + self.style.SUCCESS(f"{'✅ Created' if created else '✅ Updated'} Google SocialApp"))
            self.stdout.write(f"   Client ID: {app.client_id[:20]}...")
            self.stdout.write(f"   Secret: {app.secret[:20]}...")
            self.stdout.write(f"   Linked to Site: {site.domain}")
            
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.SUCCESS("✅ GOOGLE OAUTH SETUP COMPLETE"))
            self.stdout.write("=" * 80)
            self.stdout.write("\n" + self.style.WARNING("NEXT STEPS:"))
            self.stdout.write("1. Test local login: http://127.0.0.1:8000/login/")
            self.stdout.write("2. For production (Render):") 
            self.stdout.write("   - Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to Render environment")
            self.stdout.write("   - Redeploy the application")
            self.stdout.write("   - The migration will auto-configure on deployment\n")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ ERROR: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
            raise
