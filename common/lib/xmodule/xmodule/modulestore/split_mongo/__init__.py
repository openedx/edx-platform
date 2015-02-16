"""
General utilities
"""

from collections import namedtuple
from contracts import contract, check
from opaque_keys.edx.locator import BlockUsageLocator


class BlockKey(namedtuple('BlockKey', 'type id')):
    __slots__ = ()

    @contract(block_type="string[>0]")
    def __new__(cls, block_type, block_id):
        return super(BlockKey, cls).__new__(cls, block_type, block_id)

    @classmethod
    @contract(usage_key=BlockUsageLocator)
    def from_usage_key(cls, usage_key):
        return cls(usage_key.block_type, usage_key.block_id)


CourseEnvelope = namedtuple('CourseEnvelope', 'course_key structure')
