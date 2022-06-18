"""
Implementations of the BlockTypeKey OpaqueKey type.

This key is designed to provide a serialized format of an block_type
that encodes the block_family as well. It isn't intended for use in XBlock
ScopeIds (that block type should be a simple string, since all uses of
ScopeIds have a class associated with them).
"""
from opaque_keys.edx.keys import BlockTypeKey
from opaque_keys import InvalidKeyError

XBLOCK_V1 = 'xblock.v1'
XMODULE_V1 = 'xmodule.v1'


class BlockTypeKeyV1(BlockTypeKey):  # pylint: disable=abstract-method
    """
    A :class:`BlockTypeKey` subclass that simply stores the block_family and block_type as strings,
    and serializes them separated by a ':'.
    """
    CANONICAL_NAMESPACE = 'block-type-v1'
    KEY_FIELDS = ('block_family', 'block_type')
    __slots__ = KEY_FIELDS

    CHECKED_INIT = False

    def __init__(self, block_family, block_type):
        # Call super using kwargs, so that we can set CHECKED_INIT to False
        if ':' in block_family:
            raise InvalidKeyError(self.__class__, "block_family may not contain ':'.")
        if block_family in (XBLOCK_V1, XMODULE_V1):
            block_family = XBLOCK_V1
        super().__init__(
            block_family=block_family,
            block_type=block_type,
            deprecated=block_family == XBLOCK_V1,
        )

    @classmethod
    def _from_string(cls, serialized):
        """
        Return an instance of `cls` parsed from its `serialized` form.

        Args:
            cls: The :class:`OpaqueKey` subclass.
            serialized (unicode): A serialized :class:`OpaqueKey`, with namespace already removed.

        Raises:
            InvalidKeyError: Should be raised if `serialized` is not a valid serialized key
                understood by `cls`.
        """
        if ':' not in serialized:
            raise InvalidKeyError(
                "BlockTypeKeyV1 keys must contain ':' separating the block family from the block_type.", serialized)
        family, __, block_type = serialized.partition(':')
        return cls(family, block_type)

    def _to_string(self):
        """
        Return a serialization of `self`.

        This serialization should not include the namespace prefix.
        """
        return f"{self.block_family}:{self.block_type}"

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """
        Return an instance of `cls` parsed from its deprecated `serialized` form.

        This will be called only if :meth:`OpaqueKey.from_string` is unable to
        parse a key out of `serialized`, and only if `set_deprecated_fallback` has
        been called to register a fallback class.

        Args:
            cls: The :class:`OpaqueKey` subclass.
            serialized (unicode): A serialized :class:`OpaqueKey`, with namespace already removed.

        Raises:
            InvalidKeyError: Should be raised if `serialized` is not a valid serialized key
                understood by `cls`.
        """
        return cls(XBLOCK_V1, serialized)

    def _to_deprecated_string(self):
        """
        Return a deprecated serialization of `self`.

        This will be called only if `set_deprecated_fallback` has
        been called to register a fallback class, and the key being
        serialized has the attribute `deprecated=True`.

        This serialization should not include the namespace prefix.
        """
        return self.block_type


BlockTypeKey.set_deprecated_fallback(BlockTypeKeyV1)
