from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.conf import settings
import os

User = get_user_model()


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fix Site domain on initialization
        self._ensure_correct_site_domain()
    
    def _ensure_correct_site_domain(self):
        """Ensure the Site domain matches the current environment"""
        try:
            site_domain = os.environ.get('SITE_DOMAIN', 'farmerpricealert.onrender.com')
            site = Site.objects.get(id=settings.SITE_ID)
            
            if site.domain != site_domain:
                print(f"DEBUG: Fixing Site domain from '{site.domain}' to '{site_domain}'", flush=True)
                site.domain = site_domain
                site.name = 'Farmer Price Alert'
                site.save()
        except Site.DoesNotExist:
            print(f"DEBUG: Creating Site with domain 'farmerpricealert.onrender.com'", flush=True)
            Site.objects.create(
                id=settings.SITE_ID,
                domain='farmerpricealert.onrender.com',
                name='Farmer Price Alert'
            )
        except Exception as e:
            print(f"DEBUG: Error fixing Site domain: {str(e)}", flush=True)
    
    def on_authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        print(f"DEBUG: on_authentication_error! Provider: {provider_id}, Error: {error}, Exception: {exception}", flush=True)
        
        # Log detailed error info
        if exception:
            print(f"DEBUG: Full exception: {type(exception).__name__}: {str(exception)}", flush=True)
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}", flush=True)
        
        # Check SocialApp and Site
        try:
            from allauth.socialaccount.models import SocialApp
            from django.contrib.sites.models import Site
            
            google_app = SocialApp.objects.get(provider='google')
            print(f"DEBUG: Google SocialApp found: {google_app.name}, client_id={google_app.client_id[:10]}...", flush=True)
            print(f"DEBUG: SocialApp linked to sites: {[s.domain for s in google_app.sites.all()]}", flush=True)
            
            current_site = Site.objects.get_current()
            print(f"DEBUG: Current Site: domain='{current_site.domain}', id={current_site.id}", flush=True)
            
            request_host = request.get_host()
            print(f"DEBUG: Request host: {request_host}", flush=True)
            
        except Exception as e:
            print(f"DEBUG: Error checking SocialApp/Site: {str(e)}", flush=True)
        
        # The base class doesn't have a default implementation for this that we need to call if it errors

    def pre_social_login(self, request, sociallogin):
        """
        If a user with this email already exists, connect the social account
        """
        print(f"DEBUG: pre_social_login start for {sociallogin}", flush=True)
        if sociallogin.is_existing:
            print("DEBUG: sociallogin already exists", flush=True)
            return
        
        # Get email from social account
        email = sociallogin.account.extra_data.get('email')
        print(f"DEBUG: social email: {email}", flush=True)
        if not email:
            return
            
        # Check if user with this email exists
        try:
            user = User.objects.get(email=email)
            print(f"DEBUG: Found existing user with email {email}: {user.username}", flush=True)
            # Correct way to link to an existing user if not already logged in
            if not request.user.is_authenticated:
                sociallogin.connect(request, user)
                print("DEBUG: sociallogin.connect() called", flush=True)
        except User.DoesNotExist:
            print(f"DEBUG: No existing user found for email {email}", flush=True)
        except Exception as e:
            print(f"DEBUG: Exception in pre_social_login: {str(e)}", flush=True)

    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields from social account data
        """
        print(f"DEBUG: populate_user start. Data: {data}", flush=True)
        user = super().populate_user(request, sociallogin, data)
        
        # Generate username from email if not present
        email = data.get('email', '')
        print(f"DEBUG: User email from data: {email}", flush=True)
        if email and not user.username:
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user.username = username
            print(f"DEBUG: Generated username: {user.username}", flush=True)
        
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        print(f"DEBUG: save_user start for {user.username}", flush=True)
        # Create UserProfile if it doesn't exist
        try:
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': sociallogin.account.extra_data.get('name', ''),
                }
            )
            print(f"DEBUG: UserProfile created/found: {created}", flush=True)
        except Exception as e:
            print(f"DEBUG: Exception in save_user profile creation: {str(e)}", flush=True)
        
        return user
