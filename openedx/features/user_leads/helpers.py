from .constants import UTM_PARAM_NAMES
from .models import UserLeads


def get_utm_params(request):
    request_get_params = request.GET
    utm_params = {}

    for key in UTM_PARAM_NAMES.values():
        value = request_get_params.get(key)
        if value:
            utm_params.update({key: value})

    return utm_params


def save_user_utm(request):
    user = request.user
    origin = request.resolver_match.url_name
    utm_params = get_utm_params(request)

    if not user.is_anonymous():
        UserLeads.objects.get_or_create(user=user, origin=origin, **utm_params)
