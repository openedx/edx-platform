"""
Logic for handling actions in Studio related to Course Optimizer.
"""
import json
from user_tasks.conf import settings as user_tasks_settings
from user_tasks.models import UserTaskArtifact, UserTaskStatus

from cms.djangoapps.contentstore.tasks import CourseLinkCheckTask, LinkState
from cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers import get_xblock
from cms.djangoapps.contentstore.xblock_storage_handlers.xblock_helpers import usage_key_with_run
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore


# Restricts status in the REST API to only those which the requesting user has permission to view.
#   These can be overwritten in django settings.
#   By default, these should be the UserTaskStatus statuses:
#   'Pending', 'In Progress', 'Succeeded', 'Failed', 'Canceled', 'Retrying'
STATUS_FILTERS = user_tasks_settings.USER_TASKS_STATUS_FILTERS


def get_link_check_data(request, course_id):
    """
    Retrives data and formats it for the link check get request.
    """
    task_status = _latest_task_status(request, course_id)
    status = None
    created_at = None
    broken_links_dto = None
    error = None
    if task_status is None:
        # The task hasn't been initialized yet; did we store info in the session already?
        try:
            session_status = request.session['link_check_status']
            status = session_status[course_id]
        except KeyError:
            status = 'Uninitiated'
    else:
        status = task_status.state
        created_at = task_status.created
        if task_status.state == UserTaskStatus.SUCCEEDED:
            artifact = UserTaskArtifact.objects.get(status=task_status, name='BrokenLinks')
            with artifact.file as file:
                content = file.read()
                json_content = json.loads(content)
                broken_links_dto = generate_broken_links_descriptor(json_content, request.user)
        elif task_status.state in (UserTaskStatus.FAILED, UserTaskStatus.CANCELED):
            errors = UserTaskArtifact.objects.filter(status=task_status, name='Error')
            if errors:
                error = errors[0].text
                try:
                    error = json.loads(error)
                except ValueError:
                    # Wasn't JSON, just use the value as a string
                    pass

    data = {
        'LinkCheckStatus': status,
        **({'LinkCheckCreatedAt': created_at} if created_at else {}),
        **({'LinkCheckOutput': broken_links_dto} if broken_links_dto else {}),
        **({'LinkCheckError': error} if error else {})
    }
    return data


def _latest_task_status(request, course_key_string, view_func=None):
    """
    Get the most recent link check status update for the specified course
    key.
    """
    args = {'course_key_string': course_key_string}
    name = CourseLinkCheckTask.generate_name(args)
    task_status = UserTaskStatus.objects.filter(name=name)
    for status_filter in STATUS_FILTERS:
        task_status = status_filter().filter_queryset(request, task_status, view_func)
    return task_status.order_by('-created').first()


def generate_broken_links_descriptor(json_content, request_user):
    """
    Returns a Data Transfer Object for frontend given a list of broken links.

    ** Example json_content structure **
        Note: link_state is locked if the link is a studio link and returns 403
              link_state is external-forbidden if the link is not a studio link and returns 403
    [
        ['block_id_1', 'link_1', link_state],
        ['block_id_1', 'link_2', link_state],
        ['block_id_2', 'link_3', link_state],
        ...
    ]

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
        if rest:
            link_state = rest[0]
        else:
            link_state = ''

        usage_key = usage_key_with_run(block_id)
        block = get_xblock(usage_key, request_user)
        xblock_node_tree, xblock_dictionary = _update_node_tree_and_dictionary(
            block=block,
            link=link,
            link_state=link_state,
            node_tree=xblock_node_tree,
            dictionary=xblock_dictionary
        )

    return _create_dto_recursive(xblock_node_tree, xblock_dictionary)


def _update_node_tree_and_dictionary(block, link, link_state, node_tree, dictionary):
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
            'display_name': 'xblock name',
            'category': 'chapter'
        },
        'html_block_id': {
            'display_name': 'xblock name',
            'category': 'chapter',
            'url': 'url_1',
            'locked_links': [...],
            'broken_links': [...],
            'external_forbidden_links': [...],
        }
        ...,
    }
    """
    updated_tree, updated_dictionary = node_tree, dictionary

    path = _get_node_path(block)
    current_node = updated_tree
    xblock_id = ''

    # Traverse the path and build the tree structure
    for xblock in path:
        xblock_id = xblock.location.block_id
        updated_dictionary.setdefault(
            xblock_id,
            {
                'display_name': xblock.display_name,
                'category': getattr(xblock, 'category', ''),
            }
        )
        # Sets new current node and creates the node if it doesn't exist
        current_node = current_node.setdefault(xblock_id, {})

    # Add block-level details for the last xblock in the path (URL and broken/locked links)
    updated_dictionary[xblock_id].setdefault(
        'url',
        f'/course/{block.course_id}/editor/{block.category}/{block.location}'
    )

    # The link_state == True condition is maintained for backward compatibility.
    # Previously, the is_locked attribute was used instead of link_state.
    # If is_locked is True, it indicates that the link is locked.
    if link_state is True or link_state == LinkState.LOCKED:
        updated_dictionary[xblock_id].setdefault('locked_links', []).append(link)
    elif link_state == LinkState.EXTERNAL_FORBIDDEN:
        updated_dictionary[xblock_id].setdefault('external_forbidden_links', []).append(link)
    else:
        updated_dictionary[xblock_id].setdefault('broken_links', []).append(link)

    return updated_tree, updated_dictionary


def _get_node_path(block):
    """
    Retrieves the path from the course root node to a specific block, excluding the root.

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


def _create_dto_recursive(xblock_node, xblock_dictionary):
    """
    Recursively build the Data Transfer Object by using
    the structure from the node tree and data from the dictionary.
    """
    # Exit condition when there are no more child nodes (at block level)
    if not xblock_node:
        return None

    level = None
    xblock_children = []

    for xblock_id, node in xblock_node.items():
        child_blocks = _create_dto_recursive(node, xblock_dictionary)
        xblock_data = xblock_dictionary.get(xblock_id, {})

        xblock_entry = {
            'id': xblock_id,
            'displayName': xblock_data.get('display_name', ''),
        }
        if child_blocks is None:    # Leaf node
            level = 'blocks'
            xblock_entry.update({
                'url': xblock_data.get('url', ''),
                'brokenLinks': xblock_data.get('broken_links', []),
                'lockedLinks': xblock_data.get('locked_links', []),
                'externalForbiddenLinks': xblock_data.get('external_forbidden_links', [])
            })
        else:   # Non-leaf node
            category = xblock_data.get('category', None)
            level = CATEGORY_TO_LEVEL_MAP.get(category, None)
            xblock_entry.update(child_blocks)

        xblock_children.append(xblock_entry)

    return {level: xblock_children} if level else None


def sort_course_sections(course_key, data):
    """Retrieve and sort course sections based on the published course structure."""
    course_blocks = modulestore().get_items(
        course_key,
        qualifiers={'category': 'course'},
        revision=ModuleStoreEnum.RevisionOption.published_only
    )

    if not course_blocks or 'LinkCheckOutput' not in data or 'sections' not in data['LinkCheckOutput']:
        return data  # Return unchanged data if course_blocks or required keys are missing

    sorted_section_ids = [section.location.block_id for section in course_blocks[0].get_children()]

    sections_map = {section['id']: section for section in data['LinkCheckOutput']['sections']}
    data['LinkCheckOutput']['sections'] = [
        sections_map[section_id]
        for section_id in sorted_section_ids
        if section_id in sections_map
    ]

    return data
