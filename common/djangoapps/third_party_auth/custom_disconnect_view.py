"""
Custom disconnect view that returns JSON instead of redirecting to avoid CORS issues.
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from social_django.utils import psa
from social_django.models import UserSocialAuth


@login_required
@require_http_methods(["POST"])
@psa()
def disconnect_json_view(request, backend, association_id=None):
    """
    Custom disconnect view that returns JSON response instead of redirecting.
    This prevents CORS issues when called from MFE frontends.
    """
    user = request.user
    
    # Check URL parameter first, then query parameter for backward compatibility
    if not association_id:
        association_id = request.GET.get('association_id')
    
    try:
        if association_id:
            # Disconnect specific association by ID
            association = UserSocialAuth.objects.get(
                id=association_id,
                user=user,
                provider=backend
            )
            association.delete()
        else:
            # Disconnect all associations for this backend
            UserSocialAuth.objects.filter(
                user=user,
                provider=backend
            ).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Account successfully disconnected',
            'backend': backend,
            'association_id': association_id
        })
    
    except UserSocialAuth.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Social auth association not found',
            'backend': backend,
            'association_id': association_id
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'backend': backend,
            'association_id': association_id
        }, status=500)