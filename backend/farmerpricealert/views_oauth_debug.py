from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.conf import settings
import os
import json


@require_http_methods(["GET"])
def oauth_debug_status(request):
    """
    Debug endpoint to check OAuth configuration status
    This helps identify credential/configuration issues
    """
    
    # Only allow in development or with secret parameter
    if settings.DEBUG is False and request.GET.get('secret') != os.environ.get('DEBUG_SECRET', 'not-set'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    status = {
        'environment': {},
        'database': {},
        'configuration': {},
        'errors': []
    }
    
    # 1. Check environment variables
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    google_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    status['environment'] = {
        'GOOGLE_CLIENT_ID': {
            'is_set': bool(google_client_id),
            'length': len(google_client_id),
            'first_20_chars': google_client_id[:20] + '...' if len(google_client_id) > 20 else google_client_id,
            'has_whitespace': google_client_id != google_client_id.strip()
        },
        'GOOGLE_CLIENT_SECRET': {
            'is_set': bool(google_secret),
            'length': len(google_secret),
            'first_20_chars': google_secret[:20] + '...' if len(google_secret) > 20 else google_secret,
            'has_whitespace': google_secret != google_secret.strip()
        },
        'SITE_DOMAIN': {
            'value': os.environ.get('SITE_DOMAIN', 'farmerpricealert.onrender.com'),
        }
    }
    
    # 2. Check database SocialApp
    try:
        google_app = SocialApp.objects.get(provider='google')
        status['database']['google_socialapp'] = {
            'exists': True,
            'name': google_app.name,
            'provider': google_app.provider,
            'client_id': {
                'first_20_chars': google_app.client_id[:20] + '...' if len(google_app.client_id) > 20 else google_app.client_id,
                'length': len(google_app.client_id)
            },
            'secret': {
                'first_20_chars': google_app.secret[:20] + '...' if len(google_app.secret) > 20 else google_app.secret,
                'length': len(google_app.secret)
            },
            'linked_sites': [{'id': s.id, 'domain': s.domain} for s in google_app.sites.all()]
        }
    except SocialApp.DoesNotExist:
        status['database']['google_socialapp'] = {'exists': False}
        status['errors'].append('Google SocialApp NOT FOUND in database - OAuth will not work!')
    except Exception as e:
        status['errors'].append(f'Error checking SocialApp: {str(e)}')
    
    # 3. Check Site configuration
    try:
        site = Site.objects.get(id=settings.SITE_ID)
        status['database']['site'] = {
            'id': site.id,
            'domain': site.domain,
            'name': site.name
        }
    except Site.DoesNotExist:
        status['errors'].append(f'Site with ID {settings.SITE_ID} not found!')
    except Exception as e:
        status['errors'].append(f'Error checking Site: {str(e)}')
    
    # 4. Check Django settings
    status['configuration'] = {
        'SITE_ID': settings.SITE_ID,
        'ACCOUNT_DEFAULT_HTTP_PROTOCOL': settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL,
        'SOCIALACCOUNT_AUTO_SIGNUP': settings.SOCIALACCOUNT_AUTO_SIGNUP,
        'SOCIALACCOUNT_QUERY_EMAIL': settings.SOCIALACCOUNT_QUERY_EMAIL,
        'SOCIALACCOUNT_LOGIN_ON_GET': settings.SOCIALACCOUNT_LOGIN_ON_GET,
        'SOCIALACCOUNT_DEBUG': settings.SOCIALACCOUNT_DEBUG,
    }
    
    # 5. Perform checks
    if not status['environment']['GOOGLE_CLIENT_ID']['is_set']:
        status['errors'].append('❌ GOOGLE_CLIENT_ID environment variable is NOT SET in Render!')
    
    if not status['environment']['GOOGLE_CLIENT_SECRET']['is_set']:
        status['errors'].append('❌ GOOGLE_CLIENT_SECRET environment variable is NOT SET in Render!')
    
    if status['environment']['GOOGLE_CLIENT_ID']['has_whitespace']:
        status['errors'].append('⚠️  GOOGLE_CLIENT_ID has leading/trailing whitespace!')
    
    if status['environment']['GOOGLE_CLIENT_SECRET']['has_whitespace']:
        status['errors'].append('⚠️  GOOGLE_CLIENT_SECRET has leading/trailing whitespace!')
    
    if not status['database']['google_socialapp'].get('exists'):
        status['errors'].append('❌ Google SocialApp not created in database!')
    elif status['environment']['GOOGLE_CLIENT_ID']['is_set']:
        # Check if credentials match
        db_client_id = status['database']['google_socialapp'].get('client_id', {}).get('first_20_chars', '')
        env_client_id = status['environment']['GOOGLE_CLIENT_ID']['first_20_chars']
        if db_client_id[:20] != env_client_id[:20]:
            status['errors'].append('⚠️  Client ID in database does NOT match environment variable!')
    
    # Summary
    status['summary'] = {
        'oauth_ready': len(status['errors']) == 0,
        'error_count': len(status['errors']),
        'critical_errors': [e for e in status['errors'] if e.startswith('❌')]
    }
    
    return JsonResponse(status, json_dumps_params={'indent': 2})
