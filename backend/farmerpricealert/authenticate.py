from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

class CookieJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication using httpOnly cookies.
    Validates JWT tokens stored in request cookies.
    """
    
    def authenticate(self, request):
        # First, try to get token from Authorization header
        header = self.get_header(request)
        
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            # If no header, try to get token from cookies
            raw_token = request.COOKIES.get("access")
            
            # Handle Django REST Framework wrapped request
            if not raw_token and hasattr(request, '_request'):
                raw_token = request._request.COOKIES.get("access")

        # If no token found in either location, return None (not authenticated)
        if raw_token is None:
            return None

        try:
            # Validate the token
            validated_token = self.get_validated_token(raw_token)
            # Get the user from the token
            user = self.get_user(validated_token)
            return user, validated_token
        except InvalidToken:
            raise AuthenticationFailed("Invalid token")
        except AuthenticationFailed:
            raise
        except Exception as e:
            raise AuthenticationFailed(f"Token validation failed: {str(e)}")
