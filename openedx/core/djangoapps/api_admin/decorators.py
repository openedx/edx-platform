"""Decorators for API access management."""
from functools import wraps

from django.http import HttpResponseNotFound

from openedx.core.djangoapps.api_admin.models import ApiAccessConfig


def api_access_enabled_or_404(view):
    """If API access management feature is not enabled, return a 404."""
    @wraps(view)
    def wrapped_view(request, *args, **kwargs):
        """Wrapper for the view function."""
        if ApiAccessConfig.current().enabled:
            return view(request, *args, **kwargs)
        return HttpResponseNotFound()
    return wrapped_view
