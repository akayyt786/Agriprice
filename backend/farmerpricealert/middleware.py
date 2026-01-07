from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user as get_session_user  # Standard Django session auth
from .authenticate import CookieJWTAuthentication


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