"""Decorators for API access management."""
from functools import wraps

from django.core.urlresolvers import reverse
from django.http import HttpResponseNotFound
from django.shortcuts import redirect

from openedx.core.djangoapps.api_admin.models import ApiAccessRequest, ApiAccessConfig


def api_access_enabled_or_404(view_func):
    """If API access management feature is not enabled, return a 404."""
    @wraps(view_func)
    def wrapped_view(view_obj, *args, **kwargs):
        """Wrapper for the view function."""
        if ApiAccessConfig.current().enabled:
            return view_func(view_obj, *args, **kwargs)
        return HttpResponseNotFound()
    return wrapped_view


def require_api_access(view_func):
    """If the requesting user does not have API access, bounce them to the request form."""
    @wraps(view_func)
    def wrapped_view(view_obj, *args, **kwargs):
        """Wrapper for the view function."""
        if ApiAccessRequest.has_api_access(args[0].user):
            return view_func(view_obj, *args, **kwargs)
        return redirect(reverse('api_admin:api-request'))
    return wrapped_view
