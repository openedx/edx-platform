"""
Django template context processors.
"""
from lms.envs.common import CDN_LINK


def cdn_context(request):
    """
    CDN_LINK context for django templates.
    """
    return {
        'CDN_LINK': CDN_LINK,
    }
