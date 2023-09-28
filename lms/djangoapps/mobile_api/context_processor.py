"""
Django template context processors.
"""


from openedx.core.lib.mobile_utils import is_request_from_mobile_app


def is_from_mobile_app(request):
    """
    Configuration context for django templates.
    """
    return {
        'is_from_mobile_app': is_request_from_mobile_app(request)
    }
