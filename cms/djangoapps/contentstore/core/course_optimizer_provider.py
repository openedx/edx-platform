"""
Logic for handling actions in Studio related to Course Optimizer.
"""

import json

from cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers import get_xblock
from cms.djangoapps.contentstore.xblock_storage_handlers.xblock_helpers import usage_key_with_run


def generate_broken_links_descriptor(json_content, request_user):
    """
    Returns a Data Transfer Object for frontend given a list of broken links.

    json_content contains a list of the following:
        [block_id, link]

    Returned DTO structure:
    {
        sectionId: {
            displayName,
            subsectionId: {
                displayName,
                unitId: {
                    displayName,
                    blockId: {
                        displayName,
                        url,
                        brokenLinks: [],
                        lockedLinks: [],
                    }
                }
            }
        }
    }
    """
    dict_result = {}
    for item in json_content:
        block_id, link = item
        usage_key = usage_key_with_run(block_id)
        block = get_xblock(usage_key, request_user)
        _add_broken_link_description(dict_result, block, link)

    # print('TEST', dict_result)
    # list_result = {
    #     'sections': _transform_from_dict_to_list_format_recursive(dict_result)
    # }
    return dict_result

PARENT_CATEGORIES = ["course", "chapter", "sequential", "vertical"]
CATEGORY_TO_LEVEL = {
    "chapter": "sections",
    "sequential": "subsections",
    "vertical": "units"
}

def _add_broken_link_description(result, block, link):
    """
    Adds broken link found in the specified block along with other block data.
    Note that because the celery queue does not have credentials, some broken links will
    need to be checked client side.
    """
    bottom_up_hierarchy = []
    current = block
    while current:
        category = getattr(current, 'category', '')
        parent = current.get_parent()
        parent_category = getattr(parent, 'category', '')
        if parent_category in PARENT_CATEGORIES:
            bottom_up_hierarchy.append(current)
            current = parent
        else:
            current = None
    
    top_down_hierarchy = list(reversed(bottom_up_hierarchy))
    [section, subsection, unit, block] = top_down_hierarchy
    current_dict = result

    for xblock in top_down_hierarchy:
        # print('HIERARCHY', getattr(xblock, 'category', ''), xblock)
        # category = CATEGORY_TO_DTO_KEYS[category] if category in CATEGORY_TO_DTO_KEYS else "blocks"

        # result object
        # {
        #   sections: [
        #     {
        #         id: 'section1',
        #         displayName: 'sectionName'
        #         subsections: [
        #             {
        #                 id...
        #             }
        #         ]
        #     }
        #   ]
        # }
        if not result.get('sections', False):
            result['sections'] = []
        
        block_id = str(xblock.location.block_id)
        category = getattr(xblock, "category", "")

        if category == 'chapter':
            section_index = _find_by_id(result['sections'], block_id)
            if section_index == None:
                # append section info
                result['sections'].append(
                    {
                        'id': block_id,
                        'displayName': xblock.display_name,
                        'subsections': []
                    }
                )

        elif category == 'sequential':
            # get section index
            section_id = str(section.location.block_id)
            section_index = _find_by_id(result['sections'], section_id)

            subsection_index = _find_by_id(result['sections'][section_index]['subsections'], block_id)
            if subsection_index == None:
                # append section info
                result['sections'][section_index]['subsections'].append(
                    {
                        'id': block_id,
                        'displayName': xblock.display_name,
                        'units': []
                    }
                )
        
        elif category == 'vertical':
            # get section index
            section_id = str(section.location.block_id)
            section_index = _find_by_id(result['sections'], section_id)

            # get subsection index
            subsection_id = str(subsection.location.block_id)
            subsection_index = _find_by_id(result['sections'][section_index]['subsections'], subsection_id)

            unit_index = _find_by_id(result['sections'][section_index]['subsections'][subsection_index]['units'], block_id)
            if unit_index == None:
                # append section info
                result['sections'][section_index]['subsections'][subsection_index]['units'].append(
                    {
                        'id': block_id,
                        'displayName': xblock.display_name,
                        'blocks': []
                    }
                )
        
        else:
            # get section index
            section_id = str(section.location.block_id)
            section_index = _find_by_id(result['sections'], section_id)

            # get subsection index
            subsection_id = str(subsection.location.block_id)
            subsection_index = _find_by_id(result['sections'][section_index]['subsections'], subsection_id)

            # get unit index
            unit_id = str(unit.location.block_id)
            unit_index = _find_by_id(result['sections'][section_index]['subsections'][subsection_index]['units'], unit_id)

            block_index = _find_by_id(result['sections'][section_index]['subsections'][subsection_index]['units'][unit_index]['blocks'], block_id)
            if block_index == None:
                # append section info
                result['sections'][section_index]['subsections'][subsection_index]['units'][unit_index]['blocks'].append(
                    {
                        'id': block_id,
                        'displayName': xblock.display_name,
                        'url': f'/course/{block.course_id}/editor/{block.category}/{block.location}',
                        'brokenLinks': [],
                        'lockedLinks': []
                    }
                )
                # TODO check if lockedLinks instead
                result['sections'][section_index]['subsections'][subsection_index]['units'][unit_index]['blocks'][0]['brokenLinks'].append(link)
            else:
                # TODO check if lockedLinks instead
                result['sections'][section_index]['subsections'][subsection_index]['units'][unit_index]['blocks'][block_index]['brokenLinks'].append(link)
        
    #     current_dict = current_dict.setdefault(
    #         str(xblock.location.block_id),
    #         # getattr(xblock, "category", ""),
    #         # category,
    #         { 
    #             # 'id': str(xblock.location.block_id),
    #             'display_name': xblock.display_name,
    #             'category': getattr(xblock, 'category', ''),
    #         }
    #     )
    
    # current_dict['url'] = f'/course/{block.course_id}/editor/{block.category}/{block.location}'
    # current_dict.setdefault('broken_links', []).append(link)

def _find_by_id(data, search_id):
    """Return index. data is array"""
    for index, item in enumerate(data):
        if item.get('id') == search_id:
            return index
    return None

# def _transform_from_dict_to_list_format_recursive(data, parent_level=None):
#     """"""
#     if parent_level is None:
#         parent_level = 'subsections'

#     transformed = []
#     for key, value in data.items():
#         if key == 'category':
#             continue

#         display_name = value.get('display_name')
#         category = value.get('category')
#         level = CATEGORY_TO_LEVEL[category] if category in CATEGORY_TO_LEVEL else 'blocks'

#         entry = {
#             'id': key,
#             'displayName': display_name,
#         }
#         if level == 'blocks':
#             entry.update({
#                 'url': value.get('url'),
#                 'brokenLinks': value.get('brokenLinks', []),
#                 'lockedLinks': value.get('lockedLinks', []),
#             })
#         else:
#             child_key = level
#             child_data = {k: v for k, v in value.items() if k not in {'display_name', 'category'}}
#             entry[child_key] = _transform_from_dict_to_list_format_recursive(
#                 child_data,
#                 parent_level=level
#             )
        
#         transformed.append(entry)
    
#     return transformed
