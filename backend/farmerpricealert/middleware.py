from .authenticate import CookieJWTAuthentication
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser

def get_user_from_jwt(request):
    """
    Helper to authenticate against CookieJWTAuthentication.
    Attempts to extract and validate JWT from cookies.
    Returns User if valid, AnonymousUser if not.
    """
    authenticator = CookieJWTAuthentication()
    try:
        result = authenticator.authenticate(request)
        if result is not None:
            user, token = result
            return user
    except Exception as e:
        # Token validation failed - user is anonymous
        pass
    return AnonymousUser()

class JWTAuthMiddleware:
    """
    Middleware to authenticate users from JWT cookies for regular Django views.
    This allows both API endpoints and server-rendered pages to use JWT authentication.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Always try to authenticate from JWT, even if session exists
        # This ensures JWT takes priority over sessions
        request.user = SimpleLazyObject(lambda: get_user_from_jwt(request))

        response = self.get_response(request)
        return response
