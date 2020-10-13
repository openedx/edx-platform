"""
Helper methods of `user_leads` app
"""
from .constants import UTM_PARAM_NAMES
from .models import UserLeads


def get_utm_params(request):
    """
    Get utm parameters from `GET` request

    Arguments:
        request (HttpRequest): HttpRequest object

    Returns:
        dict: utm_params
    """
    request_get_params = request.GET
    utm_params = {}

    for key in UTM_PARAM_NAMES.values():
        value = request_get_params.get(key)
        if value:
            utm_params.update({key: value})

    return utm_params


def save_user_utm(request):
    """
    Save user utm params in `UserLeads` model

    Arguments:
        request (HttpRequest): HttpRequest object

    Returns:
        None
    """
    user = request.user
    origin = request.resolver_match.url_name
    utm_params = get_utm_params(request)

    if not user.is_anonymous():
        try:
            UserLeads.objects.get(user=user, origin=origin)
        except UserLeads.DoesNotExist:
            UserLeads.objects.create(user=user, origin=origin, **utm_params)
