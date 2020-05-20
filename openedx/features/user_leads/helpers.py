from django.db import IntegrityError, transaction

from .constants import UTM_PARAM_NAMES
from .models import UserLeads


def get_utm_params(request):
    request_get_params = request.GET
    utm_params = {}

    for key in UTM_PARAM_NAMES.values():
        utm_param = request_get_params.get(key)
        if utm_param:
            utm_params.update({key: utm_param})

    return utm_params


def save_user_utm(request):
    user = request.user
    origin = request.resolver_match.url_name
    utm_params = get_utm_params(request)

    if not user.is_anonymous():
        try:
            with transaction.atomic():
                UserLeads.objects.create(user=user, origin=origin, **utm_params)
        except IntegrityError:
            pass
