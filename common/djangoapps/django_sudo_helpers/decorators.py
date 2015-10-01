"""
Custom decorator for django-sudo.
"""
from functools import wraps
from django.conf import settings

from sudo.settings import RESET_TOKEN
from sudo.utils import new_sudo_token_on_activity
from sudo.views import redirect_to_sudo
from util.json_request import JsonResponse


def sudo_required(func_or_region):
    """
    Enforces a view to have elevated privileges.
    Should likely be paired with ``@login_required``.

    >>> @sudo_required
    >>> def secure_page(request):
    >>>     ...

    Can also specify a particular sudo region (to only
    allow access to that region).

    Also get course_id, course_key_string and library_key_string
    from kwargs and set as region if region itself is None.

    >>> @sudo_required('admin_page')
    >>> def secure_admin_page(request):
    >>>     ...
    """
    def wrapper(func):  # pylint: disable=missing-docstring
        @wraps(func)
        def inner(request, *args, **kwargs):    # pylint: disable=missing-docstring

            if not settings.FEATURES.get('ENABLE_DJANGO_SUDO', False):
                return func(request, *args, **kwargs)

            course_specific_region = kwargs.get('course_id')
            if 'course_key_string' in kwargs:
                course_specific_region = kwargs.get('course_key_string')
            if 'library_key_string' in kwargs:
                course_specific_region = kwargs.get('library_key_string')

            # N.B. region is captured from the enclosing sudo_required function
            if not request.is_sudo(region=region or course_specific_region):
                response_format = request.REQUEST.get('format', 'html')
                if (response_format == 'json' or
                        'application/json' in request.META.get('HTTP_ACCEPT', 'application/json')):
                    return JsonResponse({'error': 'Unauthorized'}, status=401)

                return redirect_to_sudo(request.get_full_path(), region=region or course_specific_region)

            if RESET_TOKEN is True:
                # Provide new sudo token content and reset timeout on activity
                new_sudo_token_on_activity(request, region=region or course_specific_region)

            return func(request, *args, **kwargs)
        return inner

    if callable(func_or_region):
        region = None
        return wrapper(func_or_region)
    else:
        region = func_or_region
        return wrapper
