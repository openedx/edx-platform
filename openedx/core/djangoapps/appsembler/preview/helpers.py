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

    preview_param = current_request.GET.get(PREVIEW_GET_PARAM, 'false')
    return str(preview_param).lower() == PREVIEW_PARAM_TRUE
