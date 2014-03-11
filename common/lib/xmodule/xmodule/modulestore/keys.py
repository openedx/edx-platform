from abc import ABCMeta, abstractmethod

from opaque_keys import OpaqueKey


class CourseKey(OpaqueKey):
    KEY_TYPE = 'course_key'

    @abstractmethod
    def org(self):
        """
        The organization that this course belongs to.
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


class UsageKey(OpaqueKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying an XBlock usage.
    """
    KEY_TYPE = 'usage_key'

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