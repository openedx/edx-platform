"""
Tahoe's custom preview mode helpers.
"""

import crum


PREVIEW_GET_PARAM = 'preview'
PREVIEW_PARAM_TRUE = 'true'


def is_preview_mode(current_request=None):
    """
    Check if the request should be shown as preview.
    """
    if not current_request:
        current_request = crum.get_current_request()

    if not current_request:
        return False

    user = getattr(current_request, 'user', None)
    if not (user and user.is_active):
        # Require a logged-in user for preview otherwise preview/live would be mixed up in caching.
        # This makes sure `preview` won't work with edx_django_utils's TieredCacheMiddleware.
        return False

    preview_param = current_request.GET.get(PREVIEW_GET_PARAM, 'false')
    return str(preview_param).lower() == PREVIEW_PARAM_TRUE
