# -*- coding: utf-8 -*-


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import ensure_csrf_cookie
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from .models import ANALYTICS_ACCESS_GROUP, ANALYTICS_LIMITED_ACCESS_GROUP

def analytics_on(func):
    def wrapper(request, *args, **kwargs):
        if not configuration_helpers.get_value('ENABLE_ANALYTICS', settings.FEATURES.get('ENABLE_ANALYTICS', False)):
            raise Http404
        else:
            return func(request, *args, **kwargs)
    return wrapper


def analytics_member_required(func):
    def wrapper(request, *args, **kwargs):
        user_groups = [group.name for group in request.user.groups.all()]
        if (ANALYTICS_ACCESS_GROUP in user_groups or ANALYTICS_LIMITED_ACCESS_GROUP in user_groups):
            return func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


@analytics_on
@login_required
@analytics_member_required
@ensure_csrf_cookie
def microsite_view(request):
    return HttpResponseNotFound()

