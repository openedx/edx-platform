import attr
from opaque_keys.edx.keys import CourseKey


class ObjectDoesNotExist(Exception):
    """
    Imitating Django model conventions, we put a subclass of this in some of our
    data classes to indicate when something is not found.
    """


@attr.s(frozen=True)
class DiscussionPluginConfigData:
    """
    Discussion Plugin Configuration Data Object
    """

    name = attr.ib(type=str)
    provider = attr.ib(type=str)
    config = attr.ib(type=dict)


@attr.s(frozen=True)
class CourseDiscussionConfigData:
    """
    Course Discussion Configuration Data Object
    """

    course_key = attr.ib(type=CourseKey)
    config_name = attr.ib(type=str)
    provider = attr.ib(type=str)
    config = attr.ib(type=dict)
    enabled = attr.ib(type=bool)

    class DoesNotExist(ObjectDoesNotExist):
        pass
