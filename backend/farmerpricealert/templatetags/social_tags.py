from django import template
from allauth.socialaccount.models import SocialApp

register = template.Library()

@register.simple_tag
def google_oauth_available():
    """
    Check if Google OAuth is configured in database
    """
    try:
        SocialApp.objects.get(provider='google')
        return True
    except SocialApp.DoesNotExist:
        return False
    except Exception:
        return False
