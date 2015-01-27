"""
General utilities
"""

from collections import namedtuple
from contracts import contract, check
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


class CourseStructure(dict):
    """
    Wrap the course structure in an object instead of using a straight Python dictionary.
    Allows the storing of meta-information about a structure that doesn't persist along with
    the structure itself.
    """
    def __init__(self, *args, **kwargs):
        super(CourseStructure, self).__init__(*args, **kwargs)
        # Set of all the loaded definitions.
        self.definitions_loaded = set()

    def is_definition_loaded(self, block):
        """
        Returns True if the block definition has been loaded.
        """
        return block in self.definitions_loaded

    def mark_definition_loaded(self, block):
        """
        Marks the block definition as loaded.
        """
        self.definitions_loaded.add(block)
