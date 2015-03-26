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


class BlockData(object):
    """
    Wrap the block data in an object instead of using a straight Python dictionary.
    Allows the storing of meta-information about a structure that doesn't persist along with
    the structure itself.
    """
    @contract(block_dict=dict)
    def __init__(self, block_dict={}):  # pylint: disable=dangerous-default-value
        # Has the definition been loaded?
        self.definition_loaded = False
        self.from_storable(block_dict)

    def to_storable(self):
        """
        Serialize to a Mongo-storable format.
        """
        return {
            'fields': self.fields,
            'block_type': self.block_type,
            'definition': self.definition,
            'defaults': self.defaults,
            'edit_info': self.edit_info
        }

    @contract(stored=dict)
    def from_storable(self, stored):
        """
        De-serialize from Mongo-storable format to an object.
        """
        self.fields = stored.get('fields', {})
        self.block_type = stored.get('block_type', None)
        self.definition = stored.get('definition', None)
        self.defaults = stored.get('defaults', {})
        self.edit_info = stored.get('edit_info', {})

    def get(self, key, *args, **kwargs):
        """
        Dict-like 'get' method. Raises AttributeError if requesting non-existent attribute and no default.
        """
        if len(args) > 0:
            return getattr(self, key, args[0])
        elif 'default' in kwargs:
            return getattr(self, key, kwargs['default'])
        else:
            return getattr(self, key)

    def __getitem__(self, key):
        """
        Dict-like '__getitem__'.
        """
        if not hasattr(self, key):
            raise KeyError
        else:
            return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        delattr(self, key)

    def __iter__(self):
        return self.__dict__.iterkeys()

    def setdefault(self, key, default=None):
        """
        Dict-like 'setdefault'.
        """
        try:
            return getattr(self, key)
        except AttributeError:
            setattr(self, key, default)
            return default
