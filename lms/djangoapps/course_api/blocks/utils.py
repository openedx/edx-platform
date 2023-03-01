"""
   Utils for Blocks
"""
from openedx.core.djangoapps.discussions.models import (
    DiscussionsConfiguration,
    Provider,
)


def filter_discussion_xblocks_from_response(response, course_key):
    """
    Removes discussion xblocks if discussion provider is openedx
    """
    configuration = DiscussionsConfiguration.get(context_key=course_key)
    provider = configuration.provider_type
    if provider == Provider.OPEN_EDX:
        response.data['blocks'] = {
            key: value
            for key, value in response.data.get('blocks', {}).items()
            if value.get('type') != 'discussion'
        }
    return response
