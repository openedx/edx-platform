"""
Logic for handling actions in Studio related to Course Optimizer.
"""

import json

from cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers import get_xblock
from cms.djangoapps.contentstore.xblock_storage_handlers.xblock_helpers import usage_key_with_run


def create_dto(json_content, request_user):
    """
    Returns a Data Transfer Object for frontend given a list of broken links.

    json_content contains a list of the following:
        [block_id, link]

    Returned DTO structure:
    {
        section: {
            display_name,
            subsection: {
                display_name,
                unit: {
                    display_name,
                    block: {
                        display_name,
                        url,
                        broken_links: [],
                    }
                }
            }
        }
    }
    """
    result = {}
    for item in json_content:
        block_id, link = item
        usage_key = usage_key_with_run(block_id)
        block = get_xblock(usage_key, request_user)
        _add_broken_link_description(result, block, link)

    return result


def _add_broken_link_description(result, block, link):
    """
    Adds broken link found in the specified block along with other block data.
    Note that because the celery queue does not have credentials, some broken links will
    need to be checked client side.
    """
    hierarchy = []
    current = block
    while current:
        hierarchy.append(current)
        current = current.get_parent()
    
    current_dict = result
    for xblock in reversed(hierarchy):
        current_dict = current_dict.setdefault(
            str(xblock.location.block_id), 
            { 'display_name': xblock.display_name }
        )
    
    current_dict['url'] = f'/course/{block.course_id}/editor/{block.category}/{block.location}'
    current_dict.setdefault('broken_links', []).append(link)