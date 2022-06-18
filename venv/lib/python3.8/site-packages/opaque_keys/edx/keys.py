"""
;
OpaqueKey abstract classes for edx-platform object types (courses, definitions, usages, and assets).
"""
import json
from abc import abstractmethod
import warnings

from opaque_keys import OpaqueKey


class LearningContextKey(OpaqueKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying a course, a library, a
    program, a website, or some other collection of content where learning
    happens.

    This concept is more generic than "course."

    A learning context does not necessarily have an org, course, or, run.
    """
    KEY_TYPE = 'context_key'
    __slots__ = ()

    # is_course: subclasses should override this to indicate whether or not this
    # key type represents a course (as opposed to a library or something else).
    # We can't just use isinstance(key, CourseKey) because LibraryLocators
    # are subclasses of CourseKey for historical reasons. Once modulestore-
    # based content libraries are removed, one can replace this with
    # just isinstance(key, CourseKey)
    is_course = False

    def make_definition_usage(self, definition_key, usage_id=None):
        """
        Return a usage key, given the given the specified definition key and
        usage_id.
        """
        raise NotImplementedError()


class CourseKey(LearningContextKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying a particular Course object.
    """
    __slots__ = ()
    is_course = True

    @property
    @abstractmethod
    def org(self):  # pragma: no cover
        """
        The organization that this course belongs to.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def course(self):  # pragma: no cover
        """
        The name for this course.

        In old-style IDs, it's the "course" in org/course/run
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def run(self):  # pragma: no cover
        """
        The run for this course.

        In old-style IDs, it's the "run" in org/course/run
        """
        raise NotImplementedError()

    @abstractmethod
    def make_usage_key(self, block_type, block_id):  # pragma: no cover
        """
        Return a usage key, given the given the specified block_type and block_id.

        This function should not actually create any new ids, but should simply
        return one that already exists.
        """
        raise NotImplementedError()

    @abstractmethod
    def make_asset_key(self, asset_type, path):  # pragma: no cover
        """
        Return an asset key, given the given the specified path.

        This function should not actually create any new ids, but should simply
        return one that already exists.
        """
        raise NotImplementedError()


class DefinitionKey(OpaqueKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying an XBlock definition.
    """
    KEY_TYPE = 'definition_key'
    __slots__ = ()

    @property
    @abstractmethod
    def block_type(self):  # pragma: no cover
        """
        The XBlock type of this definition.
        """
        raise NotImplementedError()


class CourseObjectMixin:
    """
    An abstract :class:`opaque_keys.OpaqueKey` mixin
    for keys that belong to courses.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def course_key(self):  # pragma: no cover
        """
        Return the :class:`CourseKey` for the course containing this usage.
        """
        raise NotImplementedError()

    @abstractmethod
    def map_into_course(self, course_key):  # pragma: no cover
        """
        Return a new :class:`UsageKey` or :class:`AssetKey` representing this usage inside the
        course identified by the supplied :class:`CourseKey`. It returns the same type as
        `self`

        Args:
            course_key (:class:`CourseKey`): The course to map this object into.

        Returns:
            A new :class:`CourseObjectMixin` instance.
        """
        raise NotImplementedError()


class AssetKey(CourseObjectMixin, OpaqueKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying a course asset.
    """
    KEY_TYPE = 'asset_key'
    __slots__ = ()

    @property
    @abstractmethod
    def asset_type(self):  # pragma: no cover
        """
        Return what type of asset this is.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def path(self):  # pragma: no cover
        """
        Return the path for this asset.
        """
        raise NotImplementedError()


class UsageKey(CourseObjectMixin, OpaqueKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying an XBlock usage.
    """
    KEY_TYPE = 'usage_key'
    __slots__ = ()

    @property
    @abstractmethod
    def definition_key(self):  # pragma: no cover
        """
        Return the :class:`DefinitionKey` for the XBlock containing this usage.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def block_type(self):
        """
        The XBlock type of this usage.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def block_id(self):
        """
        The name of this usage.
        """
        raise NotImplementedError()

    @property
    def context_key(self):
        """
        Get the learning context key (LearningContextKey) for this XBlock usage.
        """
        return self.course_key


class UsageKeyV2(UsageKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying an XBlock used in a specific
    learning context (e.g. a course).

    Definition + Learning Context = Usage

    UsageKeyV2 is just a subclass of UsageKey with slightly different behavior,
    but not a distinct key type (same KEY_TYPE). UsageKeyV2 should be used for
    new usage key types; the main differences between it and UsageKey are:

        * the .course_key property is considered deprecated for the new V2 key
          types, and they should implement .context_key instead.

        * the .definition_key property is explicitly disabled for V2 usage keys
    """
    __slots__ = ()

    @property
    @abstractmethod
    def context_key(self):
        """
        Get the learning context key (LearningContextKey) for this XBlock usage.
        May be a course key, library key, or some other LearningContextKey type.
        """
        raise NotImplementedError()

    @property
    def definition_key(self):
        """
        Returns the definition key for this usage. For the newer V2 key types,
        this cannot be done with the key alone, so it's necessary to ask the
        key's learning context to provide the underlying definition key.
        """
        raise AttributeError(
            "Version 2 usage keys do not support direct .definition_key access. "
            "To get the definition key within edxapp, use: "
            "get_learning_context_impl(usage_key).definition_for_usage(usage_key)"
        )

    @property
    def course_key(self):
        warnings.warn("Use .context_key instead of .course_key", DeprecationWarning, stacklevel=2)
        return self.context_key

    def map_into_course(self, course_key):
        """
        Implement map_into_course for API compatibility. Shouldn't be used in
        new code.
        """

        if course_key == self.context_key:
            return self
        raise ValueError("Cannot use map_into_course like that with this key type.")


class AsideDefinitionKey(DefinitionKey):
    """
    A definition key for an aside.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def definition_key(self):
        """
        Return the DefinitionKey that this aside is decorating.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def aside_type(self):
        """
        Return the type of this aside.
        """
        raise NotImplementedError()


class AsideUsageKey(UsageKey):
    """
    A usage key for an aside.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def usage_key(self):
        """
        Return the UsageKey that this aside is decorating.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def aside_type(self):
        """
        Return the type of this aside.
        """
        raise NotImplementedError()


# Allow class name to start with a lowercase letter
class i4xEncoder(json.JSONEncoder):  # pylint: disable=invalid-name
    """
    If provided as the cls to json.dumps, will serialize and Locations as i4x strings and other
    keys using the unicode strings.
    """
    def default(self, o):  # pylint: disable=arguments-differ, method-hidden
        if isinstance(o, OpaqueKey):
            return str(o)
        super().default(o)
        return None


class BlockTypeKey(OpaqueKey):
    """
    A key class that encodes XBlock-family block types, including which family the block
    was loaded from.
    """
    KEY_TYPE = 'block_type'
    __slots__ = ()

    @property
    @abstractmethod
    def block_family(self):
        """
        Return the block-family identifier (the entry-point used to load that block
        family).
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def block_type(self):
        """
        Return the block_type of this block (the key in the entry-point to load the block
        with).
        """
        raise NotImplementedError()
