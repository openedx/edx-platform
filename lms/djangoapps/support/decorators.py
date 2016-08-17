"""
Decorators used by the support app.
"""
from functools import wraps

from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

from courseware.access import has_access


def require_support_permission(func):
    """
    View decorator that requires the user to have permission to use the support UI.
    """
    @wraps(func)
    def inner(request, *args, **kwargs):  # pylint: disable=missing-docstring
        if has_access(request.user, "support", "global"):
            return func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    # In order to check the user's permission, he/she needs to be logged in.
    return login_required(inner)
