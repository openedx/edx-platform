"""
General utilities
"""


from collections import namedtuple

from opaque_keys.edx.locator import BlockUsageLocator


class BlockKey(namedtuple('BlockKey', 'type id')):  # lint-amnesty, pylint: disable=missing-class-docstring
    __slots__ = ()

    def __new__(cls, type, id):  # lint-amnesty, pylint: disable=redefined-builtin
        return super().__new__(cls, type, id)

    @classmethod
    def from_usage_key(cls, usage_key):
        return cls(usage_key.block_type, usage_key.block_id)


CourseEnvelope = namedtuple('CourseEnvelope', 'course_key structure')
