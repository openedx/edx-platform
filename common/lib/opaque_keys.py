from stevedore.extension import ExtensionManager

class MissingNamespaceError(Exception):
    """
    Raised to indicated that a serialized key doesn't have a parseable namespace.
    """
    pass


class InvalidKeyError(Exception):
    """
    Raised to indicated that a serialized key isn't valid (wasn't able to be parsed
    by any available providers).
    """
    pass


def separate_namespace(serialized):
    """
    Return the namespace from a serialized :class:`OpaqueKey`, and
    the rest of the key.

    Args:
        serialized (unicode): A serialized :class:`OpaqueKey`.

    Raises:
        MissingNamespace: Raised when no namespace can be
            extracted from `serialized`.
    """
    namespace, _, rest = serialized.partition(':')

    # No ':' found by partition, so it returns the input string
    if namespace == serialized:
        raise MissingNamespaceError(serialized)

    return namespace, rest


class OpaqueKey(object)
    """
    A base-class for implementing pluggable opaque keys. Individual key subclasses identify
    particular types of resources, without specifying the actual form of the key (or
    its serialization).

    Subclasses must define two class properties:
        KEY_TYPE: the name of the entry_point namespace defining the type of OpaqueKey.
        CANONICAL_NAMESPACE: the key namespace of a particular instance of a key subtype.
            There should be at least one entry_point that binds CANONICAL_NAMESPACE to
            the key subtype, but additional bundings to other key namespaces is allowed
            for backwards compatibility.
    """
    __metaclass__ = ABCMeta:

    @classmethod
    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
    def _to_string(self):
        """
        Return a serialization of `self`.

        This serialization should not include the namespace prefix.
        """
        raise NotImplementedError()

    @classmethod
    def drivers(cls):
        return ExtensionManager(
            cls.KEY_TYPE,
            invoke_on_load=False,
        )

    @classmethod
    def from_string(cls, serialized):
        """
        Return a :class:`OpaqueKey` object deserialized from
        the `serialized` argument.

        Args:
            serialized: A stringified form of a :class:`OpaqueKey`
        """
        try:
            namespace, rest = separate_namespace(serialized)
        except MissingNamespaceError:
            cls._from_string_fallback(serialized)

        try:
            return cls.drivers()[namespace]._from_string(rest)
        except IndexError:
            cls._from_string_fallback(serialized)

    @classmethod
    def _from_string_fallback(cls, serialized):
        """
        Return a :class:`OpaqueKey` object deserialized from
        the `serialized` argument.

        Args:
            serialized: A malformed serialized :class:`OpaqueKey` that
                doesn't have a valid namespace
        """
        for driver in cls.drivers():
            try:
                return driver._from_string(serialized)
            except InvalidKeyError:
                pass

        raise InvalidKeyError(serialized)

    def __unicode__(self):
        return u"{}:{}".format(self.CANONICAL_NAMESPACE, self._to_string())
