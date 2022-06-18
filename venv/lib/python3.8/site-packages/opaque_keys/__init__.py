"""
Defines the :class:`OpaqueKey` class, to be used as the base-class for
implementing pluggable OpaqueKeys.

These keys are designed to provide a limited, forward-evolveable interface to
an application, while concealing the particulars of the serialization
formats, and allowing new serialization formats to be installed transparently.
"""
from abc import ABCMeta, abstractmethod
from functools import total_ordering

# pylint: disable=wrong-import-order
from _collections import defaultdict
from stevedore.enabled import EnabledExtensionManager

__version__ = '2.3.0'


class InvalidKeyError(Exception):
    """
    Raised to indicated that a serialized key isn't valid (wasn't able to be parsed
    by any available providers).
    """
    def __init__(self, key_class, serialized):
        super().__init__(f'{key_class}: {serialized}')


class OpaqueKeyMetaclass(ABCMeta):
    """
    Metaclass for :class:`OpaqueKey`. Sets the default value for the values in ``KEY_FIELDS`` to
    ``None``.
    """
    def __new__(mcs, name, bases, attrs):  # pylint: disable=arguments-differ
        if '__slots__' not in attrs:
            for field in attrs.get('KEY_FIELDS', []):
                attrs.setdefault(field, None)
        return super().__new__(mcs, name, bases, attrs)


@total_ordering
class OpaqueKey(metaclass=OpaqueKeyMetaclass):
    """
    A base-class for implementing pluggable opaque keys. Individual key subclasses identify
    particular types of resources, without specifying the actual form of the key (or
    its serialization).

    There are two levels of expected subclasses: Key type definitions, and key implementations

    ::

        OpaqueKey
            |
        Key type
            |
        Key implementation

    The key type base class must define the class property ``KEY_TYPE``, which identifies
    which ``entry_point`` namespace the keys implementations should be registered with.

    The KeyImplementation classes must define the following:

    ``CANONICAL_NAMESPACE``
        Identifies the key namespace for the particular key implementation
        (when serializing). Key implementations must be registered using the
        ``CANONICAL_NAMESPACE`` as their entry_point name, but can also be registered
        with other names for backwards compatibility.

    ``KEY_FIELDS``
        A list of attribute names that will be used to establish object
        identity. Key implementation instances will compare equal iff all of
        their ``KEY_FIELDS`` match, and will not compare equal to instances
        of different KeyImplementation classes (even if the ``KEY_FIELDS`` match).
        These fields must be hashable.

    ``_to_string``
        Serialize the key into a unicode object. This should not include the namespace
        prefix (``CANONICAL_NAMESPACE``).

    ``_from_string``
        Construct an instance of this :class:`OpaqueKey` from a unicode object. The namespace
        will already have been parsed.

    OpaqueKeys will not have optional constructor parameters (due to the implementation of
    ``KEY_FIELDS``), by default. However, an implementation class can provide a default,
    as long as it passes that default to a call to ``super().__init__``. If the KeyImplementation
    sets the class attribute ``CHECKED_INIT`` to ``False``, then the :class:`OpaqueKey` base
    class constructor will not validate any of the ``KEY_FIELDS`` arguments, and will instead
    just expect all ``KEY_FIELDS`` to be passed as ``kwargs``.

    :class:`OpaqueKey` objects are immutable.

    Serialization of an :class:`OpaqueKey` is performed by using the :func:`unicode` builtin.
    Deserialization is performed by the :meth:`from_string` method.
    """
    __slots__ = ('_initialized', 'deprecated')

    KEY_FIELDS = []
    CANONICAL_NAMESPACE = None
    NAMESPACE_SEPARATOR = ':'
    CHECKED_INIT = True

    # ============= ABSTRACT METHODS ==============
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
        raise NotImplementedError()

    def _to_deprecated_string(self):
        """
        Return a deprecated serialization of `self`.

        This will be called only if `set_deprecated_fallback` has
        been called to register a fallback class, and the key being
        serialized has the attribute `deprecated=True`.

        This serialization should not include the namespace prefix.
        """
        raise NotImplementedError()

    # ============= SERIALIZATION ==============

    def __str__(self):
        """
        Serialize this :class:`OpaqueKey`, in the form ``<CANONICAL_NAMESPACE>:<value of _to_string>``.
        """
        if self.deprecated:
            # no namespace on deprecated
            return self._to_deprecated_string()
        return self.NAMESPACE_SEPARATOR.join([self.CANONICAL_NAMESPACE, self._to_string()])  # pylint: disable=no-member

    @classmethod
    def from_string(cls, serialized):
        """
        Return a :class:`OpaqueKey` object deserialized from
        the `serialized` argument. This object will be an instance
        of a subclass of the `cls` argument.

        Args:
            serialized: A stringified form of a :class:`OpaqueKey`
        """
        if serialized is None:
            raise InvalidKeyError(cls, serialized)

        # pylint: disable=protected-access
        # load drivers before checking for attr
        cls._drivers()
        try:
            namespace, rest = cls._separate_namespace(serialized)
            key_class = cls.get_namespace_plugin(namespace)
            if not issubclass(key_class, cls):
                # CourseKey.from_string() should never return a non-course LearningContextKey,
                # but they share the same namespace.
                raise InvalidKeyError(cls, serialized)
            return key_class._from_string(rest)
        except InvalidKeyError as error:
            if hasattr(cls, 'deprecated_fallback') and issubclass(cls.deprecated_fallback, cls):
                return cls.deprecated_fallback._from_deprecated_string(serialized)
            raise InvalidKeyError(cls, serialized) from error

    @classmethod
    def _separate_namespace(cls, serialized):
        """
        Return the namespace from a serialized :class:`OpaqueKey`, and
        the rest of the key.

        Args:
            serialized (unicode): A serialized :class:`OpaqueKey`.

        Raises:
            MissingNamespace: Raised when no namespace can be
                extracted from `serialized`.
        """
        namespace, __, rest = serialized.partition(cls.NAMESPACE_SEPARATOR)

        # If ':' isn't found in the string, then the source string
        # is returned as the first result (i.e. namespace); this happens
        # in the case of a malformed input or a deprecated string.
        if namespace == serialized:
            raise InvalidKeyError(cls, serialized)

        return (namespace, rest)

    @classmethod
    def get_namespace_plugin(cls, namespace):
        """
        Return the registered OpaqueKey subclass of cls for the supplied namespace
        """
        # The cache is stored per-calling-class, rather than per-KEY_TYPE,
        # because we should raise InvalidKeyError if the namespace
        # doesn't specify a subclass of cls

        # Ensure all extensions are loaded. Extensions may modify the deprecated_fallback attribute of the class, so
        # they must be loaded before processing any keys.
        drivers = cls._drivers()

        try:
            return drivers[namespace].plugin
        except KeyError as error:
            # Cache that the namespace doesn't correspond to a known plugin,
            # so that we don't waste time checking every time we hit
            # a particular unknown namespace (like i4x)
            raise InvalidKeyError(cls, f'{namespace}:*') from error

    LOADED_DRIVERS = defaultdict()  # If you change default, change test_default_deprecated

    @classmethod
    def _drivers(cls):
        """
        Return a driver manager for all key classes that are
        subclasses of `cls`.
        """
        if cls not in cls.LOADED_DRIVERS:
            cls.LOADED_DRIVERS[cls] = EnabledExtensionManager(
                cls.KEY_TYPE,  # pylint: disable=no-member
                check_func=lambda extension: issubclass(extension.plugin, cls),
                invoke_on_load=False,
            )
        return cls.LOADED_DRIVERS[cls]

    @classmethod
    def set_deprecated_fallback(cls, fallback):
        """
        Register a deprecated fallback class for this class to revert to.
        """
        if hasattr(cls, 'deprecated_fallback'):
            raise AttributeError(f"Error: cannot register two fallback classes for {cls!r}.")
        cls.deprecated_fallback = fallback

    # ============= VALUE SEMANTICS ==============
    def __init__(self, *args, **kwargs):
        # The __init__ expects child classes to implement KEY_FIELDS
        # pylint: disable=no-member

        # a flag used to indicate that this instance was deserialized from the
        # deprecated form and should serialize to the deprecated form
        self.deprecated = kwargs.pop('deprecated', False)  # pylint: disable=assigning-non-slot

        if self.CHECKED_INIT:
            self._checked_init(*args, **kwargs)
        else:
            self._unchecked_init(**kwargs)
        self._initialized = True  # pylint: disable=assigning-non-slot

    def _checked_init(self, *args, **kwargs):
        """
        Set all KEY_FIELDS using the contents of args and kwargs, treating
        KEY_FIELDS as the arg order, and validating number and order of args.
        """
        if len(args) + len(kwargs) != len(self.KEY_FIELDS):
            raise TypeError(
                f'__init__() takes exactly {len(self.KEY_FIELDS)} arguments ({len(args) + len(kwargs)} given)'
            )

        keyed_args = dict(zip(self.KEY_FIELDS, args))
        overlapping_args = keyed_args.keys() & kwargs.keys()
        if overlapping_args:
            raise TypeError(f'__init__() got multiple values for keyword argument {overlapping_args[0]!r}')

        keyed_args.update(kwargs)

        for key in keyed_args.keys():
            if key not in self.KEY_FIELDS:
                raise TypeError(f'__init__() got an unexpected argument {key!r}')

        self._unchecked_init(**keyed_args)

    def _unchecked_init(self, **kwargs):
        """
        Set all kwargs as attributes.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def replace(self, **kwargs):
        """
        Return: a new :class:`OpaqueKey` with ``KEY_FIELDS`` specified in ``kwargs`` replaced
            their corresponding values. Deprecation value is also preserved.

        Subclasses should override this if they have required properties that aren't included in their
        ``KEY_FIELDS``.
        """
        existing_values = {key: getattr(self, key) for key in self.KEY_FIELDS}  # pylint: disable=no-member
        existing_values['deprecated'] = self.deprecated

        if all(value == existing_values[key] for (key, value) in kwargs.items()):
            return self

        existing_values.update(kwargs)
        return type(self)(**existing_values)

    def __setattr__(self, name, value):
        if getattr(self, '_initialized', False):
            raise AttributeError(f"Can't set {name!r}. OpaqueKeys are immutable.")

        super().__setattr__(name, value)  # pylint: disable=no-member

    def __delattr__(self, name):
        raise AttributeError(f"Can't delete {name!r}. OpaqueKeys are immutable.")

    def __copy__(self):
        """
        Because it's immutable, return itself
        """
        return self

    def __deepcopy__(self, memo):
        """
        Because it's immutable, return itself
        """
        memo[id(self)] = self
        return self

    def __setstate__(self, state_dict):
        # used by pickle to set fields on an unpickled object
        for key in state_dict:
            if key in self.KEY_FIELDS:  # pylint: disable=no-member
                setattr(self, key, state_dict[key])
        self.deprecated = state_dict['deprecated']  # pylint: disable=assigning-non-slot
        self._initialized = True  # pylint: disable=assigning-non-slot

    def __getstate__(self):
        # used by pickle to get fields on an unpickled object
        pickleable_dict = {}
        for key in self.KEY_FIELDS:  # pylint: disable=no-member
            pickleable_dict[key] = getattr(self, key)
        pickleable_dict['deprecated'] = self.deprecated
        return pickleable_dict

    @property
    def _key(self):
        """Returns a tuple of key fields"""
        # pylint: disable=no-member
        return tuple(getattr(self, field) for field in self.KEY_FIELDS) + (self.CANONICAL_NAMESPACE, self.deprecated)

    def __eq__(self, other):
        return isinstance(other, OpaqueKey) and self._key == other._key  # pylint: disable=protected-access

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if (self.KEY_FIELDS, self.CANONICAL_NAMESPACE, self.deprecated) != (other.KEY_FIELDS, other.CANONICAL_NAMESPACE,
                                                                            other.deprecated):
            raise TypeError(f"{self!r} is incompatible with {other!r}")
        return self._key < other._key  # pylint: disable=protected-access

    def __hash__(self):
        return hash(self._key)

    def __repr__(self):
        key_field_repr = ', '.join(repr(getattr(self, key)) for key in self.KEY_FIELDS)
        return f'{self.__class__.__name__}({key_field_repr})'

    def __len__(self):
        """Return the number of characters in the serialized OpaqueKey"""
        return len(str(self))
