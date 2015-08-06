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


def filter_by_scheme(course_user_partitions, filter_partition_schemes):
    """ Filter all user partitions for 'course_user_partitions' which have
    scheme present in list 'filter_partition_schemes'.

    Args:
        course_user_partitions (List): List of user partitions
        filter_partition_schemes (List): List of user partitions scheme names

    Returns:
        List of filtered user partitions.

    """
    filtered_user_partitions = []
    for user_partition in course_user_partitions:
        if user_partition.scheme.name not in filter_partition_schemes:
            filtered_user_partitions.append(user_partition)

    return filtered_user_partitions
