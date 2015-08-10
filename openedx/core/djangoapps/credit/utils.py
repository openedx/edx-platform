"""
Common utility methods useful for credit app.
"""

from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum


def is_in_course_tree(block):
    """ Check that the XBlock is in the course tree.

    It is possible that the XBlock is not in the course tree if its parent has
    been deleted and is now an orphan.

    Args:
        block (xblock): XBlock mixin

    Returns:
        bool: True or False
    """
    ancestor = block.get_parent()
    while ancestor is not None and ancestor.location.category != "course":
        ancestor = ancestor.get_parent()

    return ancestor is not None


def get_course_xblocks(course_key, category):
    """ Retrieve all XBlocks in the course for a particular category.

    Args:
        course_key (CourseKey): Identifier for the course
        category (str): Category of XBlock

    Returns:
        List of XBlocks that are published and haven't been deleted.

    """
    xblocks = [
        block for block in modulestore().get_items(
            course_key,
            qualifiers={"category": category},
            revision=ModuleStoreEnum.RevisionOption.published_only,
        )
        if is_in_course_tree(block)
    ]

    return xblocks


def filter_by_scheme(course_user_partitions, filter_partition_scheme):
    """ Filter all user partitions for 'course_user_partitions' which have
    scheme name as provided 'filter_partition_scheme'.

    Args:
        course_user_partitions (List): List of user partitions
        filter_partition_scheme (str): User partition scheme name

    Returns:
        List of filtered user partitions.

    """
    filtered_user_partitions = []
    for user_partition in course_user_partitions:
        if not user_partition.scheme.name == filter_partition_scheme:
            filtered_user_partitions.append(user_partition)

    return filtered_user_partitions


def get_group_access_blocks(course_key):
    """ Returns list of course blocks which have group access.

    Args:
        course_key (CourseKey): Identifier for the course

    Returns:
        List of xblocks.

    """
    items = modulestore().get_items(course_key, settings={'group_access': {'$exists': True}})

    return items
