"""
Custom disconnect view that returns JSON instead of redirecting to avoid CORS issues.
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import DatabaseError
from social_django.utils import psa
from social_django.models import UserSocialAuth


@login_required
@require_http_methods(["POST"])
@psa()
def disconnect_json_view(request, backend, association_id=None):
    """
    Custom disconnect view that returns JSON response instead of redirecting.
    """
    user = request.user
    # Check URL parameter first, then POST parameter
    if not association_id:
        association_id = request.POST.get('association_id')
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
        error_response = JsonResponse({
            'success': False,
            'error': 'Social auth association not found',
            'backend': backend,
            'association_id': association_id
        }, status=404)
    except (ValueError, TypeError):
        error_response = JsonResponse({
            'success': False,
            'error': 'Invalid association_id parameter',
            'backend': backend,
            'association_id': association_id
        }, status=400)
    except DatabaseError:
        error_response = JsonResponse({
            'success': False,
            'error': 'Database operation failed',
            'backend': backend,
            'association_id': association_id
        }, status=500)
    except ValidationError:
        error_response = JsonResponse({
            'success': False,
            'error': 'Validation failed',
            'backend': backend,
            'association_id': association_id
        }, status=400)
    except PermissionDenied:
        error_response = JsonResponse({
            'success': False,
            'error': 'Permission denied',
            'backend': backend,
            'association_id': association_id
        }, status=403)
    return error_response
