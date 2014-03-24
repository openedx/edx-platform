from abc import abstractmethod, abstractproperty

from opaque_keys import OpaqueKey
from xblock.runtime import IdReader


class CourseKey(OpaqueKey):
    KEY_TYPE = 'course_key'
    __slots__ = ()

    @abstractproperty
    def org(self):
        """
        The organization that this course belongs to.
        """
        raise NotImplementedError()

    @abstractproperty
    def offering(self):
        """
        The offering identifier for this course.

        This is complement of the org; in old-style IDs, "course/run"
        """
        raise NotImplementedError()

    @abstractmethod
    def make_usage_key(self, block_type, block_id):
        """
        Return a usage key, given the given the specified block_type and block_id.

        This function should not actually create any new ids, but should simply
        return one that already exists.
        """
        raise NotImplementedError()

    @abstractmethod
    def make_asset_key(self, asset_type, path):
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

    @abstractmethod
    def block_type(self):
        """
        The XBlock type of this definition.
        """
        raise NotImplementedError()


class CourseObjectMixin(object):
    """
    An abstract :class:`opaque_keys.OpaqueKey` mixin
    for keys that belong to courses.
    """
    __slots__ = ()

    @abstractproperty
    def course_key(self):
        """
        Return the :class:`CourseKey` for the course containing this usage.
        """
        raise NotImplementedError()

    @abstractmethod
    def map_into_course(self, course_key):
        """
        Return a new :class:`UsageKey` representing this usage inside the
        course identified by the supplied :class:`CourseKey`.
        """
        raise NotImplementedError()


class AssetKey(CourseObjectMixin, OpaqueKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying a course asset.
    """
    KEY_TYPE = 'asset_key'
    __slots__ = ()

    @abstractproperty
    def path(self):
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

    @abstractproperty
    def definition_key(self):
        """
        Return the :class:`DefinitionKey` for the XBlock containing this usage.
        """
        raise NotImplementedError()


class OpaqueKeyReader(IdReader):
    """
    IdReader for :class:`DefinitionKey` and :class:`UsageKey`s.
    """
    def get_definition_id(self, usage_id):
        return usage_id.definition_key

    def get_block_type(self, def_id):
        return def_id.block_type
