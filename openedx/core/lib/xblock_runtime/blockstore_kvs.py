from xblock.fields import Scope

from xmodule.modulestore.inheritance import InheritanceKeyValueStore


class BlockstoreKVS(InheritanceKeyValueStore):
    """
    A KeyValueStore that reads XBlock field data directly out of Blockstore.
    Note that this is considered too slow for use in the LMS, but is fine
    for authoring.
    """

    VALID_SCOPES = (Scope.parent, Scope.children, Scope.settings, Scope.content)

    def __init__(self):
        """
        Initialize the Blockstore KVS. This is long-lived object and
        can be used as a singleton - only one instance is ever needed.
        """

    def get(self, key):
        # get default which may be the inherited value
        raise KeyError()

    def set(self, key, value):
        raise NotImplementedError()

    def delete(self, key):
        raise NotImplementedError()

    def has(self, key):
        """
        Is the given field explicitly set in this kvs (neither inherited nor default)
        """
        # handle any special cases
        if key.scope not in self.VALID_SCOPES:
            return False
        return False

    def default(self, key):
        """
        Get the default value for this field which may depend on context or may just be the field's global
        default. The default behavior is to raise KeyError which will cause the caller to return the field's
        global default.
        """
        raise KeyError()
