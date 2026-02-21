from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Debug OAuth configuration'

    def handle(self, *args, **options):
        """Debug OAuth settings"""
        print("\n" + "="*80)
        print("OAUTH DEBUG REPORT")
        print("="*80)
        
        # 1. Check environment variables
        print("\n1. ENVIRONMENT VARIABLES:")
        print("-" * 80)
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID', 'NOT SET')
        google_secret = os.environ.get('GOOGLE_CLIENT_SECRET', 'NOT SET')
        
        print(f"GOOGLE_CLIENT_ID: {google_client_id}")
        print(f"  Length: {len(google_client_id) if google_client_id != 'NOT SET' else 'N/A'}")
        print(f"  Has leading/trailing spaces: {google_client_id != google_client_id.strip() if google_client_id != 'NOT SET' else 'N/A'}")
        
        print(f"\nGOOGLE_CLIENT_SECRET: {google_secret}")
        print(f"  Length: {len(google_secret) if google_secret != 'NOT SET' else 'N/A'}")
        print(f"  Has leading/trailing spaces: {google_secret != google_secret.strip() if google_secret != 'NOT SET' else 'N/A'}")
        
        # 2. Check what's in the database
        print("\n2. DATABASE SOCIALAPP:")
        print("-" * 80)
        try:
            google_app = SocialApp.objects.get(provider='google')
            print(f"SocialApp exists: YES")
            print(f"  Name: {google_app.name}")
            print(f"  Provider: {google_app.provider}")
            print(f"  Client ID: {google_app.client_id}")
            print(f"    Length: {len(google_app.client_id)}")
            print(f"    Has leading/trailing spaces: {google_app.client_id != google_app.client_id.strip()}")
            print(f"  Secret: {google_app.secret}")
            print(f"    Length: {len(google_app.secret)}")
            print(f"    Has leading/trailing spaces: {google_app.secret != google_app.secret.strip()}")
            print(f"  Linked sites: {list(google_app.sites.values_list('domain', flat=True))}")
        except SocialApp.DoesNotExist:
            print("SocialApp exists: NO - Google SocialApp not found in database!")
        except Exception as e:
            print(f"Error retrieving SocialApp: {str(e)}")
        
        # 3. Check Site configuration
        print("\n3. SITE CONFIGURATION:")
        print("-" * 80)
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            print(f"Site ID: {settings.SITE_ID}")
            print(f"Site domain: {site.domain}")
            print(f"Site name: {site.name}")
        except Site.DoesNotExist:
            print(f"Site with ID {settings.SITE_ID} does NOT exist!")
        except Exception as e:
            print(f"Error retrieving Site: {str(e)}")
        
        # 4. Check if they match
        print("\n4. CREDENTIAL COMPARISON:")
        print("-" * 80)
        if google_client_id != 'NOT SET' and google_secret != 'NOT SET':
            try:
                google_app = SocialApp.objects.get(provider='google')
                
                client_id_match = google_app.client_id == google_client_id.strip()
                secret_match = google_app.secret == google_secret.strip()
                
                print(f"Client ID matches environment: {client_id_match}")
                if not client_id_match:
                    print(f"  Expected: {google_client_id.strip()}")
                    print(f"  Got:      {google_app.client_id}")
                
                print(f"Secret matches environment: {secret_match}")
                if not secret_match:
                    print(f"  Expected: {google_secret.strip()}")
                    print(f"  Got:      {google_app.secret}")
                
            except SocialApp.DoesNotExist:
                print("Cannot compare - SocialApp doesn't exist in database!")
        else:
            print("Cannot compare - environment variables not set!")
        
        print("\n" + "="*80)
        print("END OF DEBUG REPORT")
        print("="*80 + "\n")
