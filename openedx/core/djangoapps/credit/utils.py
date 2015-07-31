"""
Utilities for the credit app.
"""
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore


def get_course_blocks(course_key, category):
    """
    Retrieve all XBlocks in the course for a particular category.

    Returns only XBlocks that are published and haven't been deleted.
    """
    return [
        block for block in modulestore().get_items(
            course_key,
            qualifiers={"category": category},
            revision=ModuleStoreEnum.RevisionOption.published_only,
        )
        if _is_in_course_tree(block)
    ]


def _is_in_course_tree(block):
    """
    Check that the XBlock is in the course tree.

    It's possible that the XBlock is not in the course tree
    if its parent has been deleted and is now an orphan.
    """
    ancestor = block.get_parent()
    while ancestor is not None and ancestor.location.category != "course":
        ancestor = ancestor.get_parent()

    return ancestor is not None
