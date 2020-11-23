"""
Appsembler: Module to have `is_request_has_valid_api_key` to break circular dependency.
"""

from django.conf import settings

from edx_django_utils.monitoring import set_custom_metric
from openedx.core.lib.log_utils import audit_log


def is_request_has_valid_api_key(request):
    """
    Check for permissions by matching the configured API key and header
    Allow the request if and only if settings.EDX_API_KEY is set and
    the X-Edx-Api-Key HTTP header is present in the request and
    matches the setting.

    Appsembler: This is moved from ApiKeyHeaderPermission. If that
                class was changed by upstream, it will give us git
                merge issues.
    """
    api_key = getattr(settings, "EDX_API_KEY", None)

    if api_key is not None and request.META.get("HTTP_X_EDX_API_KEY") == api_key:
        audit_log("ApiKeyHeaderPermission used",
                  path=request.path,
                  ip=request.META.get("REMOTE_ADDR"))
        set_custom_metric('deprecated_api_key_header', True)
        return True

    return False
