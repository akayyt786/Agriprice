from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user as get_session_user  # Import standard Django session auth
from .authenticate import CookieJWTAuthentication

def get_user_unified(request):
    """
    Authentication Logic:
    1. Try to authenticate via JWT Cookie (your custom login).
    2. If that fails (returns None or errors), try standard Django Session (used by Google Login).
    3. If both fail, return AnonymousUser (handled by get_session_user default).
    """
    
    # 1. Try JWT Authentication first
    authenticator = CookieJWTAuthentication()
    try:
        # authenticate() returns (user, token) if successful, or None
        result = authenticator.authenticate(request)
        if result is not None:
            user, token = result
            return user
    except Exception:
        # If JWT fails (expired, invalid, or missing), just pass.
        # We don't want to crash; we want to try the next method.
        pass
        
    # 2. Fallback to Standard Session Authentication
    # This checks request.session, which is where Allauth stores the Google user.
    return get_session_user(request)

class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Overwrite request.user with our unified helper.
        # SimpleLazyObject ensures the code only runs when request.user is actually accessed.
        request.user = SimpleLazyObject(lambda: get_user_unified(request))
        
        return self.get_response(request)