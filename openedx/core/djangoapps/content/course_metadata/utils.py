"""
Utility methods for course metadata app
"""
from django.conf import settings

from xmodule.modulestore.django import modulestore


def get_course_leaf_nodes(course_key):
    """
    Get count of the leaf nodes with ability to exclude some categories
    """
    nodes = []
    detached_categories = getattr(settings, 'PROGRESS_DETACHED_CATEGORIES', [])
    store = modulestore()
    verticals = store.get_items(course_key, qualifiers={'category': 'vertical'})
    orphans = store.get_orphans(course_key)
    for vertical in verticals:
        if hasattr(vertical, 'children') and vertical.location not in orphans:
            nodes.extend([unit for unit in vertical.children
                          if getattr(unit, 'category') not in detached_categories])
    return nodes
