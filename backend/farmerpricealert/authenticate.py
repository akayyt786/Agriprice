from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        
        if header is None:
            raw_token = request.COOKIES.get("access")
            if not raw_token and hasattr(request, '_request'):
                raw_token = request._request.COOKIES.get("access")
            
            # Show all cookies for debugging
            cookies_list = list(request.COOKIES.keys())
            if not cookies_list and hasattr(request, '_request'):
                cookies_list = list(request._request.COOKIES.keys())
            
            print(f"--- DEBUG: No Header found")
            print(f"--- DEBUG: All Cookies received: {cookies_list}")
            print(f"--- DEBUG: 'access' cookie found: {bool(raw_token)}")
        else:
            raw_token = self.get_raw_token(header)
            print(f"--- DEBUG: Header found, Token present: {bool(raw_token)}")

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            print("--- DEBUG: Token validated successfully")
            user = self.get_user(validated_token)
            print(f"--- DEBUG: User authenticated: {user}")
            return user, validated_token
        except Exception as e:
            print(f"--- DEBUG: Token validation failed: {str(e)}")
            return None
