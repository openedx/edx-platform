"""
Custom field types for mongoengine
"""
import mongoengine
from opaque_keys.edx.locations import SlashSeparatedCourseKey, Location
from types import NoneType
from opaque_keys.edx.keys import CourseKey, UsageKey


class CourseKeyField(mongoengine.StringField):
    """
    Serializes and deserializes CourseKey's to mongo dbs which use mongoengine
    """
    def __init__(self, **kwargs):
        # it'd be useful to add init args such as support_deprecated, force_deprecated
        super(CourseKeyField, self).__init__(**kwargs)

    def to_mongo(self, course_key):
        """
        For now saves the course key in the deprecated form
        """
        assert isinstance(course_key, (NoneType, CourseKey))
        if course_key:
            # don't call super as base.BaseField.to_mongo calls to_python() for some odd reason
            return course_key.to_deprecated_string()
        else:
            return None

    def to_python(self, course_key):
        """
        Deserialize to a CourseKey instance
        """
        # calling super b/c it decodes utf (and doesn't have circularity of from_python)
        course_key = super(CourseKeyField, self).to_python(course_key)
        assert isinstance(course_key, (NoneType, basestring, CourseKey))
        if course_key == '':
            return None
        if isinstance(course_key, basestring):
            return SlashSeparatedCourseKey.from_deprecated_string(course_key)
        else:
            return course_key

    def validate(self, value):
        assert isinstance(value, (NoneType, basestring, CourseKey))
        if isinstance(value, CourseKey):
            return super(CourseKeyField, self).validate(value.to_deprecated_string())
        else:
            return super(CourseKeyField, self).validate(value)

    def prepare_query_value(self, _opt, value):
        return self.to_mongo(value)


class UsageKeyField(mongoengine.StringField):
    """
    Represent a UsageKey as a single string in Mongo
    """
    def to_mongo(self, location):
        """
        For now saves the usage key in the deprecated location i4x/c4x form
        """
        assert isinstance(location, (NoneType, UsageKey))
        if location is None:
            return None
        return super(UsageKeyField, self).to_mongo(location.to_deprecated_string())

    def to_python(self, location):
        """
        Deserialize to a UsageKey instance: for now it's a location missing the run
        """
        assert isinstance(location, (NoneType, basestring, UsageKey))
        if location == '':
            return None
        if isinstance(location, basestring):
            location = super(UsageKeyField, self).to_python(location)
            return Location.from_deprecated_string(location)
        else:
            return location

    def validate(self, value):
        assert isinstance(value, (NoneType, basestring, UsageKey))
        if isinstance(value, UsageKey):
            return super(UsageKeyField, self).validate(value.to_deprecated_string())
        else:
            return super(UsageKeyField, self).validate(value)

    def prepare_query_value(self, _opt, value):
        return self.to_mongo(value)
