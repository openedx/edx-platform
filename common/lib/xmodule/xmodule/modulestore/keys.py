from abc import abstractmethod

from opaque_keys import OpaqueKey


class CourseKey(OpaqueKey):
    KEY_TYPE = 'course_key'

    @abstractmethod
    def org(self):
        """
        The organization that this course belongs to.
        """
        raise NotImplementedError()

    @abstractmethod
    def run(self):
        """
        The run identifier for this course.
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
    def make_asset_key(self, path):
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    def definition_key(self):
        """
        Return the :class:`DefinitionKey` for the XBlock containing this usage.
        """
        raise NotImplementedError()
