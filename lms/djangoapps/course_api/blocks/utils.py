"""
   Utils for Blocks
"""
from rest_framework.utils.serializer_helpers import ReturnList

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
        # Finding ids of discussion xblocks
        if isinstance(response.data, ReturnList):
            discussion_xblocks = [
                value.get('id') for value in response.data if value.get('type') == 'discussion'
            ]
        else:
            discussion_xblocks = [
                key for key, value in response.data.get('blocks', {}).items()
                if value.get('type') == 'discussion'
            ]
        # Filtering discussion xblocks keys from blocks
        if isinstance(response.data, ReturnList):
            filtered_blocks = {
                value.get('id'): value
                for value in response.data
                if value.get('type') != 'discussion'
            }
        else:
            filtered_blocks = {
                key: value
                for key, value in response.data.get('blocks', {}).items()
                if value.get('type') != 'discussion'
            }
        # Removing reference of discussion xblocks from unit
        # These references needs to be removed because they no longer exist
        for _, block_data in filtered_blocks.items():
            for key in ['descendants', 'children']:
                descendants = block_data.get(key, [])
                if descendants:
                    descendants = [
                        descendant for descendant in descendants
                        if descendant not in discussion_xblocks
                    ]
                    block_data[key] = descendants
        if isinstance(response.data, ReturnList):
            response.data = filtered_blocks
        else:
            response.data['blocks'] = filtered_blocks
    return response
