from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Setup social apps from environment variables'

    def handle(self, *args, **options):
        # First, ensure the Site domain is correct
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            site_domain = os.environ.get('SITE_DOMAIN', 'farmerpricealert.onrender.com')
            if site.domain != site_domain:
                site.domain = site_domain
                site.name = 'Farmer Price Alert'
                site.save()
                self.stdout.write(self.style.SUCCESS(f'Updated Site domain to {site_domain}'))
        except Site.DoesNotExist:
            site = Site.objects.create(
                id=settings.SITE_ID,
                domain=os.environ.get('SITE_DOMAIN', 'farmerpricealert.onrender.com'),
                name='Farmer Price Alert'
            )
            self.stdout.write(self.style.SUCCESS(f'Created Site with domain {site.domain}'))

        # Get Google credentials from environment
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
        google_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        
        if not google_client_id or not google_secret:
            self.stdout.write(self.style.WARNING('GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set. Skipping Google OAuth setup.'))
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
            if site not in app.sites.all():
                app.sites.add(site)
            
            if created:
                self.stdout.write(self.style.SUCCESS('Successfully created Google SocialApp'))
            else:
                # Update existing app
                app.client_id = google_client_id
                app.secret = google_secret
                app.save()
                self.stdout.write(self.style.SUCCESS('Successfully updated Google SocialApp'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up Google OAuth: {str(e)}'))
