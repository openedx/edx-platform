"""
Custom disconnect view that returns JSON instead of redirecting to avoid CORS issues.
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import DatabaseError
from social_django.utils import load_strategy, load_backend
from social_django.models import UserSocialAuth


@login_required
@require_http_methods(["POST"])
def disconnect_json_view(request, backend, association_id=None):
    """
    Custom disconnect view that returns JSON response instead of redirecting.
    """
    user = request.user
    # Check URL parameter first, then POST parameter
    if not association_id:
        association_id = request.POST.get('association_id')
    
    try:
        # Load the backend strategy and backend instance
        strategy = load_strategy(request)
        backend_instance = load_backend(strategy, backend, redirect_uri=request.build_absolute_uri())
        
        # Use backend.disconnect method - simplified approach without partial pipeline
        response = backend_instance.disconnect(user=user, association_id=association_id)
        
        # Always return JSON response regardless of what backend.disconnect returns
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
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'Invalid association_id parameter',
            'backend': backend,
            'association_id': association_id
        }, status=400)
    except DatabaseError:
        return JsonResponse({
            'success': False,
            'error': 'Database operation failed',
            'backend': backend,
            'association_id': association_id
        }, status=500)
    except ValidationError:
        return JsonResponse({
            'success': False,
            'error': 'Validation failed',
            'backend': backend,
            'association_id': association_id
        }, status=400)
    except PermissionDenied:
        return JsonResponse({
            'success': False,
            'error': 'Permission denied',
            'backend': backend,
            'association_id': association_id
        }, status=403)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Disconnect failed: {str(e)}',
            'backend': backend,
            'association_id': association_id
        }, status=500)
