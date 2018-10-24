from opaque_keys import OpaqueKey, InvalidKeyError

from .usage_locator import GlobalUsageLocator

class LearningContextKey(OpaqueKey):
    """
    A key that idenitifies a course, a library, a program,
    or some other collection of content where learning happens.
    """
    KEY_TYPE = 'context_key'
    __slots__ = ()

    def make_usage_key(self, definition_key, usage_id=None):
        """
        Return a usage key, given the given the specified definition key and usage_id
        This function should not actually create any new ids, but should simply
        return one that already exists.
        """
        raise NotImplementedError()


class GlobalContextLocator(LearningContextKey):
    """
    A key for the "global context", which means viewing some
    block definition directly (e.g. in a library/bundle) and
    not as part of a course or other context.
    """
    CANONICAL_NAMESPACE = 'gcl'
    KEY_FIELDS = ()
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False
    KEY_VALUE = u'global'

    def __init__(self):
        super(GlobalContextLocator, self).__init__()

    def _to_string(self):
        return self.KEY_VALUE

    @classmethod
    def _from_string(cls, serialized):
        if (serialized != cls.KEY_VALUE):
            raise InvalidKeyError(cls, serialized)
        return cls()

    def make_usage_key(self, definition_key, usage_id=None):
        """
        Return a usage key, given the given the specified definition key and usage_id
        This function should not actually create any new ids, but should simply
        return one that already exists.
        """
        if usage_id is not None:
            raise ValueError("Cannot have a usage_id in the global context")
        return GlobalUsageLocator(definition_key)

global_context = GlobalContextLocator()
