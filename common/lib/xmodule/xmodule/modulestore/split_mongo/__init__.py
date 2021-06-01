"""
General utilities
"""


from collections import namedtuple

from contracts import check, contract
from opaque_keys.edx.locator import BlockUsageLocator


class BlockKey(namedtuple('BlockKey', 'type id')):
    __slots__ = ()

    @contract(type="string[>0]")
    def __new__(cls, type, id):
        return super(BlockKey, cls).__new__(cls, type, id)

    @classmethod
    @contract(usage_key=BlockUsageLocator)
    def from_usage_key(cls, usage_key):
        return cls(usage_key.block_type, usage_key.block_id)


CourseEnvelope = namedtuple('CourseEnvelope', 'course_key structure')
