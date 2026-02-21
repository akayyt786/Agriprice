from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user as get_session_user  # Standard Django session auth
from .authenticate import CookieJWTAuthentication
from django.contrib.sites.models import Site
from django.conf import settings
import os


class EnsureSiteDomainMiddleware:
    """Ensure Site domain matches current environment before any OAuth processing"""
    def __init__(self, get_response):
        self.get_response = get_response
        self._ensure_site_domain()
    
    def _ensure_site_domain(self):
        """Fix Site domain on app startup"""
        try:
            site_domain = os.environ.get('SITE_DOMAIN', 'farmerpricealert.onrender.com')
            site = Site.objects.get(id=settings.SITE_ID)
            
            if site.domain != site_domain:
                print(f"🔧 Middleware: Fixing Site domain from '{site.domain}' to '{site_domain}'", flush=True)
                site.domain = site_domain
                site.name = 'Farmer Price Alert'
                site.save()
        except Site.DoesNotExist:
            print(f"🔧 Middleware: Creating Site with domain 'farmerpricealert.onrender.com'", flush=True)
            Site.objects.create(
                id=settings.SITE_ID,
                domain='farmerpricealert.onrender.com',
                name='Farmer Price Alert'
            )
        except Exception as e:
            print(f"⚠️ Middleware: Error fixing Site domain: {str(e)}", flush=True)
    
    def __call__(self, request):
        return self.get_response(request)


def get_user_unified(request):
    """
    Authentication Logic:
    1. For /admin, skip JWT and rely on Django session (admin/staff).
    2. Otherwise, try JWT Cookie.
    3. Fallback to standard Django Session.
    """
    # Let admin use only session auth (avoids being “logged in” as a non-staff JWT user)
    if request.path.startswith("/admin"):
        return get_session_user(request)

    # Try JWT Authentication first
    authenticator = CookieJWTAuthentication()
    try:
        result = authenticator.authenticate(request)
        if result is not None:
            user, token = result
            return user
    except Exception:
        # If JWT fails (expired/invalid/missing), fall through to session
        pass

    # Fallback to Standard Session Authentication
    return get_session_user(request)


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # SimpleLazyObject defers execution until request.user is accessed
        request.user = SimpleLazyObject(lambda: get_user_unified(request))
        return self.get_response(request)