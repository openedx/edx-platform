"""
This file provides implementations of :class:`.AsideDefinitionKey` and :class:`.AsideUsageKey`.

:class:`.AsideUsageKeyV2` stores a :class:`.UsageKey` and an `aside_type`, and serializes as
`<usage_key>::<aside_type>`.

Likewise, :class:`.AsideDefinitionKeyV2` stores a :class:`.DefinitionKey` and an `aside_type',
and serializes as `<definition_key>::<aside_type>`.

:class:`.AsideUsageKeyV1` and :class:`.AsideDefinitionKeyV1` use a similar encoding strategy
as the V2 versions, but are unable to handle particular edge-cases.

See :class:`xblock.fields.BlockScope` for a description of what data definitions and usages
describe. The `AsideDefinitionKey` and `AsideUsageKey` allow :class:`xblock.core.XBlockAside`s to
store scoped data alongside the definition and usage of the particular XBlock usage that they're
commenting on.
"""
import re

from opaque_keys.edx.keys import AsideDefinitionKey, AsideUsageKey, DefinitionKey, UsageKey
from opaque_keys import InvalidKeyError


def _encode_v1(value):
    """
    Encode all '::' substrings in a string (also encodes '$' so that it can
    be used to mark encoded characters). This way we can use :: to separate
    the two halves of an aside key.
    """
    simple = value.replace('$', '$$').replace('::', '$::')
    return simple


def _decode_v1(value):
    """
    Decode '::' and '$' characters encoded by `_encode`.
    """
    decode_colons = value.replace('$::', '::')
    decode_dollars = decode_colons.replace('$$', '$')

    reencoded = _encode_v1(decode_dollars)
    if reencoded != value:
        raise ValueError(f'Ambiguous encoded value, {value!r} could have been encoded as {reencoded!r}')

    return decode_dollars


def _join_keys_v1(left, right):
    """
    Join two keys into a format separable by using _split_keys_v1.
    """
    if left.endswith(':') or '::' in left:
        raise ValueError("Can't join a left string ending in ':' or containing '::'")
    return f"{_encode_v1(left)}::{_encode_v1(right)}"


def _split_keys_v1(joined):
    """
    Split two keys out a string created by _join_keys_v1.
    """
    left, _, right = joined.partition('::')
    return _decode_v1(left), _decode_v1(right)


def _encode_v2(value):
    """
    Encode all ':' substrings in a string (also encodes '$' so that it can
    be used to mark encoded characters). This way we can use :: to separate
    the two halves of an aside key.
    """
    simple = value.replace('$', '$$').replace(':', '$:')
    return simple


def _decode_v2(value):
    """
    Decode ':' and '$' characters encoded by `_encode`.
    """
    if re.search(r'(?<!\$):', value):
        raise ValueError("Unescaped ':' in the encoded string")

    decode_colons = value.replace('$:', ':')

    if re.search(r'(?<!\$)(\$\$)*\$([^$]|\Z)', decode_colons):
        raise ValueError("Unescaped '$' in encoded string")
    return decode_colons.replace('$$', '$')


def _join_keys_v2(left, right):
    """
    Join two keys into a format separable by using _split_keys_v2.
    """
    return f"{_encode_v2(left)}::{_encode_v2(right)}"


def _split_keys_v2(joined):
    """
    Split two keys out a string created by _join_keys_v2.
    """
    left, _, right = joined.rpartition('::')
    return _decode_v2(left), _decode_v2(right)


class AsideDefinitionKeyV2(AsideDefinitionKey):  # pylint: disable=abstract-method
    """
    A definition key for an aside.
    """
    CANONICAL_NAMESPACE = 'aside-def-v2'
    KEY_FIELDS = ('definition_key', 'aside_type')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    DEFINITION_KEY_FIELDS = ('block_type', )

    def __init__(self, definition_key, aside_type, deprecated=False):
        super().__init__(definition_key=definition_key, aside_type=aside_type, deprecated=deprecated)

    @property
    def block_type(self):
        return self.definition_key.block_type

    def replace(self, **kwargs):
        """
        Return: a new :class:`AsideDefinitionKeyV2` with ``KEY_FIELDS`` specified in ``kwargs`` replaced
            with their corresponding values. Deprecation value is also preserved.
        """
        if 'definition_key' in kwargs:
            for attr in self.DEFINITION_KEY_FIELDS:
                kwargs.pop(attr, None)
        else:
            kwargs['definition_key'] = self.definition_key.replace(**{
                key: kwargs.pop(key)
                for key
                in self.DEFINITION_KEY_FIELDS
                if key in kwargs
            })
        return super().replace(**kwargs)

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
        try:
            def_key, aside_type = _split_keys_v2(serialized)
            return cls(DefinitionKey.from_string(def_key), aside_type)
        except ValueError as exc:
            raise InvalidKeyError(cls, exc.args) from exc

    def _to_string(self):
        """
        Return a serialization of `self`.

        This serialization should not include the namespace prefix.
        """
        return _join_keys_v2(str(self.definition_key), str(self.aside_type))


class AsideDefinitionKeyV1(AsideDefinitionKeyV2):  # pylint: disable=abstract-method
    """
    A definition key for an aside.
    """
    CANONICAL_NAMESPACE = 'aside-def-v1'

    def __init__(self, definition_key, aside_type, deprecated=False):
        serialized_def_key = str(definition_key)
        if '::' in serialized_def_key or serialized_def_key.endswith(':'):
            raise ValueError("Definition keys containing '::' or ending with ':' break the v1 parsing code")
        super().__init__(definition_key=definition_key, aside_type=aside_type, deprecated=deprecated)

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
        try:
            def_key, aside_type = _split_keys_v1(serialized)
            return cls(DefinitionKey.from_string(def_key), aside_type)
        except ValueError as exc:
            raise InvalidKeyError(cls, exc.args) from exc

    def _to_string(self):
        """
        Return a serialization of `self`.

        This serialization should not include the namespace prefix.
        """
        return _join_keys_v1(str(self.definition_key), str(self.aside_type))


class AsideUsageKeyV2(AsideUsageKey):  # pylint: disable=abstract-method
    """
    A usage key for an aside.
    """
    CANONICAL_NAMESPACE = 'aside-usage-v2'
    KEY_FIELDS = ('usage_key', 'aside_type')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    USAGE_KEY_ATTRS = ('block_id', 'block_type', 'definition_key', 'course_key')

    def __init__(self, usage_key, aside_type, deprecated=False):
        super().__init__(usage_key=usage_key, aside_type=aside_type, deprecated=deprecated)

    @property
    def block_id(self):
        return self.usage_key.block_id

    @property
    def block_type(self):
        return self.usage_key.block_type

    @property
    def definition_key(self):
        return self.usage_key.definition_key

    @property
    def course_key(self):
        """
        Return the :class:`CourseKey` for the course containing this usage.
        """
        return self.usage_key.course_key

    def map_into_course(self, course_key):
        """
        Return a new :class:`UsageKey` or :class:`AssetKey` representing this usage inside the
        course identified by the supplied :class:`CourseKey`. It returns the same type as
        `self`

        Args:
            course_key (:class:`CourseKey`): The course to map this object into.

        Returns:
            A new :class:`CourseObjectMixin` instance.
        """
        return self.replace(usage_key=self.usage_key.map_into_course(course_key))

    def replace(self, **kwargs):
        """
        Return: a new :class:`AsideUsageKeyV2` with ``KEY_FIELDS`` specified in ``kwargs`` replaced
            with their corresponding values. Deprecation value is also preserved.
        """
        if 'usage_key' in kwargs:
            for attr in self.USAGE_KEY_ATTRS:
                kwargs.pop(attr, None)
        else:
            kwargs['usage_key'] = self.usage_key.replace(**{
                key: kwargs.pop(key)
                for key
                in self.USAGE_KEY_ATTRS
                if key in kwargs
            })
        return super().replace(**kwargs)

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
        try:
            usage_key, aside_type = _split_keys_v2(serialized)
            return cls(UsageKey.from_string(usage_key), aside_type)
        except ValueError as exc:
            raise InvalidKeyError(cls, exc.args) from exc

    def _to_string(self):
        """
        Return a serialization of `self`.

        This serialization should not include the namespace prefix.
        """
        return _join_keys_v2(str(self.usage_key), str(self.aside_type))


class AsideUsageKeyV1(AsideUsageKeyV2):  # pylint: disable=abstract-method
    """
    A usage key for an aside.
    """
    CANONICAL_NAMESPACE = 'aside-usage-v1'

    def __init__(self, usage_key, aside_type, deprecated=False):
        serialized_usage_key = str(usage_key)
        if '::' in serialized_usage_key or serialized_usage_key.endswith(':'):
            raise ValueError("Usage keys containing '::' or ending with ':' break the v1 parsing code")
        super().__init__(usage_key=usage_key, aside_type=aside_type, deprecated=deprecated)

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
        try:
            usage_key, aside_type = _split_keys_v1(serialized)
            return cls(UsageKey.from_string(usage_key), aside_type)
        except ValueError as exc:
            raise InvalidKeyError(cls, exc.args) from exc

    def _to_string(self):
        """
        Return a serialization of `self`.

        This serialization should not include the namespace prefix.
        """
        return _join_keys_v1(str(self.usage_key), str(self.aside_type))
