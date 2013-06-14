"""
This module handles loading xmodule templates
These templates are used by the CMS to provide baseline content that
gives sample field values when adding new modules to a course.

`Template`s are defined in x_module. They contain 3 attributes:
    metadata: A dictionary with the template metadata
    data: A JSON value that defines the template content
"""

# TODO should this move to cms since it's really only for module crud?
import logging

from collections import defaultdict
from .x_module import XModuleDescriptor

log = logging.getLogger(__name__)


def all_templates():
    """
    Returns all templates for enabled modules, grouped by descriptor type
    """
    # TODO use memcache to memoize w/ expiration
    templates = defaultdict(list)
    for category, descriptor in XModuleDescriptor.load_classes():
        templates[category] = descriptor.templates()

    return templates
