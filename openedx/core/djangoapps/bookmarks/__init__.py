"""
Bookmarks module.
"""
from __future__ import absolute_import

from collections import namedtuple

DEFAULT_FIELDS = [
    'id',
    'course_id',
    'usage_id',
    'block_type',
    'created',
]

OPTIONAL_FIELDS = [
    'display_name',
    'path',
]

PathItem = namedtuple('PathItem', ['usage_key', 'display_name'])
