import warnings

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from .bundle_def import BundleDefinitionLocator


class BlockUsageKeyV2(UsageKey):
    """
    Abstract base class that encodes an XBlock used in a specific
    context (e.g. a course)
    """
    @property
    def context_key(self):
        raise NotImplementedError()

    @property
    def course_key(self):
        warnings.warn("Use .context_key instead of .course_key", DeprecationWarning, stacklevel=2)
        return self.context_key


class GlobalUsageLocator(BlockUsageKeyV2):
    """
    Encodes an XBlock (definition) used directly, not in any specific context
    """
    CANONICAL_NAMESPACE = 'gblock-v1'
    KEY_FIELDS = ('definition_key', )
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False


    def __init__(self, definition_key):
        """
        Construct a GlobalUsageLocator
        """
        if not isinstance(definition_key, BundleDefinitionLocator):
            raise TypeError("GlobalUsageLocator only works with BundleDefinitionLocator")
        super(GlobalUsageLocator, self).__init__(definition_key=definition_key)
    
    def block_type(self):
        """
        The XBlock type of this usage.
        e.g. 'html'
        """
        return self.definition_key.block_type

    @property
    def block_id(self):
        """
        All usage keys must implement 'block_id', though it's less relevant for blocks in
        the global scope. Return our definition key instead and raise a warning.
        (We generally want code to use this key as a whole, not looking at its constituent
        parts like block_id, which require assumptions about how these keys work.)
        """
        warnings.warn("Using .block_id of a GlobalUsageLocator is not recommended.", DeprecationWarning, stacklevel=2)
        return self.definition_key._to_string()

    def _to_string(self):
        """
        Serialize this key as a string
        """
        return self.definition_key._to_string()

    @classmethod
    def _from_string(cls, serialized):
        definition_key = BundleDefinitionLocator._from_string(serialized)
        return cls(definition_key=definition_key)
