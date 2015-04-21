"""
Discussion API internal interface
"""
from collections import defaultdict

from django_comment_client.utils import get_accessible_discussion_modules


def get_course_topics(course, user):
    """
    Return the course topic listing for the given course and user.

    Parameters:

    course: The course to get topics for
    user: The requesting user, for access control

    Returns:

    A course topic listing dictionary; see discussion_api.views.CourseTopicViews
    for more detail.
    """
    def get_module_sort_key(module):
        """
        Get the sort key for the module (falling back to the discussion_target
        setting if absent)
        """
        return module.sort_key or module.discussion_target

    discussion_modules = get_accessible_discussion_modules(course, user)
    modules_by_category = defaultdict(list)
    for module in discussion_modules:
        modules_by_category[module.discussion_category].append(module)
    courseware_topics = [
        {
            "id": None,
            "name": category,
            "children": [
                {
                    "id": module.discussion_id,
                    "name": module.discussion_target,
                    "children": [],
                }
                for module in sorted(modules_by_category[category], key=get_module_sort_key)
            ],
        }
        for category in sorted(modules_by_category.keys())
    ]

    non_courseware_topics = [
        {
            "id": entry["id"],
            "name": name,
            "children": [],
        }
        for name, entry in sorted(
            course.discussion_topics.items(),
            key=lambda item: item[1].get("sort_key", item[0])
        )
    ]

    return {
        "courseware_topics": courseware_topics,
        "non_courseware_topics": non_courseware_topics,
    }
