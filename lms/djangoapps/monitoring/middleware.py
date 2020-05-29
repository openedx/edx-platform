"""
Middleware for monitoring the LMS
"""
import re
import time
from django.conf import settings
from edx_django_utils.monitoring import set_custom_metric


class CodeOwnerMetricMiddleware:
    """
    Django middleware object to set custom metric for the owner of each view.

    Uses the Django Setting CODE_OWNER_MAPPINGS. This setting should contain a
    list of lists, where the inner lists contain two elements, the dotted prefix
    path and the second contains code owner. The view function's module is
    checked to see if it starts with any of the configured paths.

    For example::

        CODE_OWNER_MAPPINGS = [
            ['xblock_django', 'team-red'],
            ['openedx.core.djangoapps.xblock', 'team-red'],
            ['badges', 'team-blue'],
        ]

    Note: A view function with module 'badges.views' would map to 'team-blue'.

    Custom metrics set:
    - code_owner: The owning team mapped to the current view.
    - code_owner_mapping_error: If there are any errors when trying to perform the mapping.
    - code_owner_mapping_time: The time it took to perform the mapping to help ensure
        there are no performance issues while mapping.
    - view_func_module: The __module__ of the view_func, which can be used to
        find missing mappings.

    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Set custom metric for the code_owner of the view if configured to do so.
        """
        if not hasattr(settings, 'CODE_OWNER_MAPPINGS') or not settings.CODE_OWNER_MAPPINGS:
            return

        before_time = time.perf_counter()
        try:
            set_custom_metric('view_func_module', view_func.__module__)
            # Note: No pre-processing is currently done to enhance the mapping speed
            # because the complexity doesn't seem necessary. A time metric is provided
            # to ensure that this remains true.
            for module_prefix, code_owner in settings.CODE_OWNER_MAPPINGS:
                if self._check_view_matches_prefix(view_func, module_prefix):
                    set_custom_metric('code_owner', code_owner)
                    break
        except Exception as e:
            set_custom_metric('code_owner_mapping_error', e)

        after_time = time.perf_counter()
        # Tracking the compute time enables us to alert when optimization is required.
        set_custom_metric('code_owner_mapping_time', round(after_time - before_time, 4))

    def _check_view_matches_prefix(self, view_func, module_prefix):
        """
        Returns True iff module_prefix is a proper prefix of the view_func's module.
        """
        view_func_module = _get_view_func_module(view_func)
        if not view_func_module.startswith(module_prefix):
            return False

        # ensure a module like 'test_middleware' would match:
        #   'test_middleware' or 'test_middleware.views'
        # but not match:
        #   'test_middleware_2` or 'test'
        pattern = r'''
            ^                   # beginning of string
            {module_prefix}     # format string replacement
            (
                \.              # either a literal period
            |                   # or
                \b              # end of line (won't contain spaces)
            )
        '''.format(module_prefix=module_prefix)
        if re.match(pattern, view_func_module, re.VERBOSE):
            return True

        return False


def _get_view_func_module(view_func):
    """
    Returns the view_func's __module__.  Enables mocking.
    """
    return view_func.__module__
