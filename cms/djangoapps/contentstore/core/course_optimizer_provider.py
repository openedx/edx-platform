"""
Logic for handling actions in Studio related to Course Optimizer.
"""
import json

from opaque_keys.edx.keys import CourseKey
from user_tasks.conf import settings as user_tasks_settings
from user_tasks.models import UserTaskArtifact, UserTaskStatus

from cms.djangoapps.contentstore.tasks import CourseLinkCheckTask, LinkState, extract_content_URLs_from_course
from cms.djangoapps.contentstore.utils import create_course_info_usage_key
from cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers import get_xblock
from cms.djangoapps.contentstore.xblock_storage_handlers.xblock_helpers import usage_key_with_run
from openedx.core.lib.xblock_utils import get_course_update_items
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.tabs import StaticTab

# Restricts status in the REST API to only those which the requesting user has permission to view.
#   These can be overwritten in django settings.
#   By default, these should be the UserTaskStatus statuses:
#   'Pending', 'In Progress', 'Succeeded', 'Failed', 'Canceled', 'Retrying'
STATUS_FILTERS = user_tasks_settings.USER_TASKS_STATUS_FILTERS


def get_link_check_data(request, course_id):
    """
    Retrives data and formats it for the link check get request.
    """
    course_key = CourseKey.from_string(course_id)
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
                broken_links_dto = generate_broken_links_descriptor(json_content, request.user, course_key)
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


def generate_broken_links_descriptor(json_content, request_user, course_key):
    """
    Returns a Data Transfer Object for frontend given a list of broken links.
    Includes all link types: broken, locked, external-forbidden, and previous run links,
    as well as links found in course updates, handouts, and custom pages.

    ** Example json_content structure **
        Note: link_state is locked if the link is a studio link and returns 403
              link_state is external-forbidden if the link is not a studio link and returns 403
              link_state is previous-run if the link points to a previous course run
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
                                        'previousRunLinks: []
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
        ],
        'course_updates': [
            {
                'name': 'published_date',
                'url': 'url',
                'brokenLinks': [],
                'lockedLinks': [],
                'externalForbiddenLinks': [],
                'previousRunLinks': []
            },
            ...
            {
                'name': 'handouts',
                'url': 'url',
                'brokenLinks': [],
                'lockedLinks': [],
                'externalForbiddenLinks': [],
                'previousRunLinks': []
            }
        ],
        'custom_pages': [
            {
                'name': 'page_name',
                'url': 'url',
                'brokenLinks': [],
                'lockedLinks': [],
                'externalForbiddenLinks': [],
                'previousRunLinks': []
            },
            ...
        ]
    }
    """
    return _generate_enhanced_links_descriptor(json_content, request_user, course_key)


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
    elif link_state == LinkState.PREVIOUS_RUN:
        updated_dictionary[xblock_id].setdefault('previous_run_links', []).append(link)
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


def _create_dto_recursive(xblock_node, xblock_dictionary, parent_id=None):
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
        child_blocks = _create_dto_recursive(node, xblock_dictionary, parent_id=xblock_id)
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
                'externalForbiddenLinks': xblock_data.get('external_forbidden_links', []),
                'previousRunLinks': xblock_data.get('previous_run_links', [])
            })
        else:   # Non-leaf node
            category = xblock_data.get('category', None)
            # If parent and child has same IDs and level is 'sections', change it to 'subsections'
            # And if parent and child has same IDs and level is 'subsections', change it to 'units'
            if xblock_id == parent_id:
                if category == "chapter":
                    category = "sequential"
                elif category == "sequential":
                    category = "vertical"
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


def _generate_links_descriptor_for_content(json_content, request_user):
    """
    Creates a content tree of all links in a course and their states
    Returns a structure containing all broken links and locked links for a course.
    """
    xblock_node_tree = {}
    xblock_dictionary = {}

    for item in json_content:
        block_id, link, *rest = item
        if rest:
            link_state = rest[0]
        else:
            link_state = ""

        usage_key = usage_key_with_run(block_id)
        block = get_xblock(usage_key, request_user)
        xblock_node_tree, xblock_dictionary = _update_node_tree_and_dictionary(
            block=block,
            link=link,
            link_state=link_state,
            node_tree=xblock_node_tree,
            dictionary=xblock_dictionary,
        )

    result = _create_dto_recursive(xblock_node_tree, xblock_dictionary)
    # Ensure we always return a valid structure with sections
    if not isinstance(result, dict):
        result = {"sections": []}

    return result


def _generate_enhanced_links_descriptor(json_content, request_user, course_key):
    """
    Generate enhanced link descriptor that includes course updates, handouts, and custom pages.
    """

    content_links = []
    course_updates_links = []
    handouts_links = []
    custom_pages_links = []
    course = modulestore().get_course(course_key)

    for item in json_content:
        block_id, link, *rest = item
        if "course_info" in block_id and "updates" in block_id:
            course_updates_links.append(item)
        elif "course_info" in block_id and "handouts" in block_id:
            handouts_links.append(item)
        elif "static_tab" in block_id:
            custom_pages_links.append(item)
        else:
            content_links.append(item)

    try:
        main_content = _generate_links_descriptor_for_content(content_links, request_user)
    except Exception:   # pylint: disable=broad-exception-caught
        main_content = {"sections": []}

    course_updates_data = (
        _generate_course_updates_structure(course, course_updates_links)
        if course_updates_links and course else []
    )

    handouts_data = (
        _generate_handouts_structure(course, handouts_links)
        if handouts_links and course else []
    )

    custom_pages_data = (
        _generate_custom_pages_structure(course, custom_pages_links)
        if custom_pages_links and course else []
    )

    result = main_content.copy()
    result["course_updates"] = course_updates_data + handouts_data
    result["custom_pages"] = custom_pages_data
    return result


def _generate_enhanced_content_structure(course, content_links, content_type):
    """
    Unified function to generate structure for enhanced content (updates, handouts, custom pages).

    Args:
        course: Course object
        content_links: List of link items for this content type
        content_type: 'updates', 'handouts', or 'custom_pages'

    Returns:
        List of content items with categorized links
    """
    result = []
    try:
        if content_type == "custom_pages":
            result = _generate_custom_pages_content(course, content_links)
        elif content_type == "updates":
            result = _generate_course_updates_content(course, content_links)
        elif content_type == "handouts":
            result = _generate_handouts_content(course, content_links)
        return result
    except Exception as e:   # pylint: disable=broad-exception-caught
        return result


def _generate_course_updates_content(course, updates_links):
    """Generate course updates content with categorized links."""
    store = modulestore()
    usage_key = create_course_info_usage_key(course, "updates")
    updates_block = store.get_item(usage_key)
    course_updates = []

    if not (updates_block and hasattr(updates_block, "data")):
        return course_updates

    update_items = get_course_update_items(updates_block)
    if not update_items:
        return course_updates

    # Create link state mapping
    link_state_map = {
        item[1]: item[2] if len(item) >= 3 else LinkState.BROKEN
        for item in updates_links if len(item) >= 2
    }

    for update in update_items:
        if update.get("status") != "deleted":
            update_content = update.get("content", "")
            update_links = extract_content_URLs_from_course(update_content) if update_content else []

            # Match links with their states
            update_link_data = _create_empty_links_data()
            for link in update_links:
                link_state = link_state_map.get(link)
                if link_state is not None:
                    _categorize_link_by_state(link, link_state, update_link_data)

            course_updates.append(
                {
                    "id": str(update.get("id")),
                    "displayName": update.get("date", "Unknown Date"),
                    "url": f"/course/{str(course.id)}/course_info",
                    **update_link_data,
                }
            )

    return course_updates


def _generate_handouts_content(course, handouts_links):
    """Generate handouts content with categorized links."""
    store = modulestore()
    usage_key = create_course_info_usage_key(course, "handouts")
    handouts_block = store.get_item(usage_key)
    course_handouts = []

    if not (
        handouts_block
        and hasattr(handouts_block, "data")
        and handouts_block.data
    ):
        return course_handouts

    # Create link state mapping for handouts
    link_state_map = {
        item[1]: item[2] if len(item) >= 3 else LinkState.BROKEN
        for item in handouts_links if len(item) >= 2
    }

    links_data = _create_empty_links_data()
    for link, link_state in link_state_map.items():
        _categorize_link_by_state(link, link_state, links_data)

    course_handouts = [
        {
            "id": str(usage_key),
            "displayName": "handouts",
            "url": f"/course/{str(course.id)}/course_info",
            **links_data,
        }
    ]
    return course_handouts


def _generate_custom_pages_content(course, custom_pages_links):
    """Generate custom pages content with categorized links."""
    custom_pages = []

    if not course or not hasattr(course, "tabs"):
        return custom_pages

    # Group links by block_id and categorize them
    links_by_page = {}
    for item in custom_pages_links:
        if len(item) >= 2:
            block_id, link = item[0], item[1]
            link_state = item[2] if len(item) >= 3 else LinkState.BROKEN
            links_by_page.setdefault(block_id, _create_empty_links_data())
            _categorize_link_by_state(link, link_state, links_by_page[block_id])

    # Process static tabs and add their pages
    for tab in course.tabs:
        if isinstance(tab, StaticTab):
            block_id = str(course.id.make_usage_key("static_tab", tab.url_slug))
            custom_pages.append({
                "id": block_id,
                "displayName": tab.name,
                "url": f"/course/{str(course.id)}/custom-pages",
                **links_by_page.get(block_id, _create_empty_links_data()),
            })

    return custom_pages


def _generate_course_updates_structure(course, updates_links):
    """Generate structure for course updates."""
    return _generate_enhanced_content_structure(course, updates_links, "updates")


def _generate_handouts_structure(course, handouts_links):
    """Generate structure for course handouts."""
    return _generate_enhanced_content_structure(course, handouts_links, "handouts")


def _generate_custom_pages_structure(course, custom_pages_links):
    """Generate structure for custom pages (static tabs)."""
    return _generate_enhanced_content_structure(
        course, custom_pages_links, "custom_pages"
    )


def _categorize_link_by_state(link, link_state, links_data):
    """
    Helper function to categorize a link into the appropriate list based on its state.

    Args:
        link (str): The URL link to categorize
        link_state (str): The state of the link (broken, locked, external-forbidden, previous-run)
        links_data (dict): Dictionary containing the categorized link lists
    """
    state_to_key = {
        LinkState.BROKEN: "brokenLinks",
        LinkState.LOCKED: "lockedLinks",
        LinkState.EXTERNAL_FORBIDDEN: "externalForbiddenLinks",
        LinkState.PREVIOUS_RUN: "previousRunLinks"
    }

    key = state_to_key.get(link_state)
    if key:
        links_data[key].append(link)


def _create_empty_links_data():
    """
    Helper function to create an empty links data structure.

    Returns:
        dict: Dictionary with empty lists for each link type
    """
    return {
        "brokenLinks": [],
        "lockedLinks": [],
        "externalForbiddenLinks": [],
        "previousRunLinks": [],
    }
