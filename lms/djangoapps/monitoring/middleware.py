"""
Middleware for monitoring the LMS
"""
import logging
from edx_django_utils.monitoring import set_custom_metric

from .utils import get_code_owner_from_module, is_code_owner_mappings_configured

log = logging.getLogger(__name__)


class CodeOwnerMetricMiddleware:
    """
    Django middleware object to set custom metrics for the owner of each view.

    Custom metrics set:
    - code_owner: The owning team mapped to the current view.
    - code_owner_mapping_error: If there are any errors when trying to perform the mapping.
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
        if not is_code_owner_mappings_configured():
            return

        try:
            view_func_module = view_func.__module__
            set_custom_metric('view_func_module', view_func_module)
            code_owner = get_code_owner_from_module(view_func_module)
            if code_owner:
                set_custom_metric('code_owner', code_owner)
        except Exception as e:
            set_custom_metric('code_owner_mapping_error', e)
