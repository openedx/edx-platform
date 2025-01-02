"""
Logic for handling actions in Studio related to Course Optimizer.
"""

import json

from cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers import get_xblock
from cms.djangoapps.contentstore.xblock_storage_handlers.xblock_helpers import usage_key_with_run


def generate_broken_links_descriptor(json_content, request_user):
    """
    Returns a Data Transfer Object for frontend given a list of broken links.

    json_content contains a list of [block_id, link, is_locked]
        is_locked is true if the link is a studio link and returns 403 on request

    ** Example DTO structure **
    {
        'sections': [
            {
                'id': 'section_id',
                'displayName': 'section name',
                'subsections': [
                    {
                        'id': 'subsection_id',
                        'displayName': 'subsection name',
                        'units': [
                            {
                                'id': 'unit_id',
                                'displayName': 'unit name',
                                'blocks': [
                                    {
                                        'id': 'block_id',
                                        'displayName': 'block name',
                                        'url': 'url/to/block',
                                        'brokenLinks: [],
                                        'lockedLinks: [],
                                    },
                                    ...,
                                ]
                            },
                            ...,
                        ]
                    },
                    ...,
                ]
            },
            ...,
        ]
    }
    """
    xblock_node_tree = {}   # tree representation of xblock relationships
    xblock_dictionary = {}  # dictionary of xblock attributes

    for item in json_content:
        block_id, link, *rest = item
        is_locked_flag = bool(rest[0])

        usage_key = usage_key_with_run(block_id)
        block = get_xblock(usage_key, request_user)
        _update_node_tree_and_dictionary(
            block=block,
            link=link,
            is_locked=is_locked_flag,
            node_tree=xblock_node_tree,
            dictionary=xblock_dictionary
        )

    return _create_dto_from_node_tree_recursive(xblock_node_tree, xblock_dictionary)


def _update_node_tree_and_dictionary(block, link, is_locked, node_tree, dictionary):
    """
    Inserts a block into the node tree and add its attributes to the dictionary.

    ** Example node tree structure **
    {
        'section_id1': {
            'subsection_id1': {
                'unit_id1': {
                    'block_id1': {},
                    'block_id2': {},
                    ...,
                },
                'unit_id2': {
                    'block_id3': {},
                    ...,
                },
                ...,
            },
            ...,
        },
        ...,
    }

    ** Example dictionary structure **
    {
        'xblock_id: {
            'display_name': 'xblock name'
            'category': 'html'
        },
        ...,
    }
    """
    path = _get_node_path(block)
    current_node = node_tree
    xblock_id = ''

    # Traverse the path and build the tree structure
    for xblock in path:
        xblock_id = xblock.location.block_id
        dictionary.setdefault(xblock_id,
            { 
                'display_name': xblock.display_name,
                'category': getattr(xblock, 'category', ''),
            }
        )
        # Sets new current node and creates the node if it doesn't exist
        current_node = current_node.setdefault(xblock_id, {})
    
    # Add block-level details for the last xblock in the path (URL and broken/locked links)
    dictionary[xblock_id].setdefault('url',
        f'/course/{block.course_id}/editor/{block.category}/{block.location}'
    )
    if is_locked:
        dictionary[xblock_id].setdefault('locked_links', []).append(link)
    else:
        dictionary[xblock_id].setdefault('broken_links', []).append(link)


def _get_node_path(block):
    """
    Retrieves the path frmo the course root node to a specific block, excluding the root.

    ** Example Path structure **
    [chapter_node, sequential_node, vertical_node, html_node]
    """
    path = []
    current_node = block

    while current_node.get_parent():
        path.append(current_node)
        current_node = current_node.get_parent()
    
    return list(reversed(path))


CATEGORY_TO_LEVEL_MAP = {
    "chapter": "sections",
    "sequential": "subsections",
    "vertical": "units"
}


def _create_dto_from_node_tree_recursive(xblock_node, xblock_dictionary):
    """
    Recursively build the Data Transfer Object from the node tree and dictionary.
    """
    # Exit condition when there are no more child nodes (at block level)
    if not xblock_node:
        return None

    level = None
    xblock_children = []

    for xblock_id, node in xblock_node.items():
        child_blocks = _create_dto_from_node_tree_recursive(node, xblock_dictionary)
        xblock_data = xblock_dictionary.get(xblock_id, {})

        xblock_entry = {
            'id': xblock_id,
            'displayName': xblock_data.get('display_name', ''),
        }
        if child_blocks == None:    # Leaf node
            level = 'blocks'
            xblock_entry.update({
                'url': xblock_data.get('url', ''),
                'brokenLinks': xblock_data.get('broken_links', []),
                'lockedLinks': xblock_data.get('locked_links', []),
            })
        else:   # Non-leaf node
            category = xblock_data.get('category', None)
            level = CATEGORY_TO_LEVEL_MAP.get(category, None)
            xblock_entry.update(child_blocks)

        xblock_children.append(xblock_entry)

    return {level: xblock_children} if level else None
