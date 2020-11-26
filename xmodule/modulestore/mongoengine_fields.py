"""
Custom field types for mongoengine
"""


import mongoengine
import six

from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import Location
from six import text_type


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
        assert isinstance(course_key, (type(None), CourseKey))
        if course_key:
            # don't call super as base.BaseField.to_mongo calls to_python() for some odd reason
            return text_type(course_key)
        else:
            return None

    def to_python(self, course_key):
        """
        Deserialize to a CourseKey instance
        """
        # calling super b/c it decodes utf (and doesn't have circularity of from_python)
        course_key = super(CourseKeyField, self).to_python(course_key)
        assert isinstance(course_key, (type(None), six.string_types, CourseKey))
        if course_key == '':
            return None
        if isinstance(course_key, six.string_types):
            return CourseKey.from_string(course_key)
        else:
            return course_key

    def validate(self, value):
        assert isinstance(value, (type(None), six.string_types, CourseKey))
        if isinstance(value, CourseKey):
            return super(CourseKeyField, self).validate(text_type(value))
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
        assert isinstance(location, (type(None), UsageKey))
        if location is None:
            return None
        return super(UsageKeyField, self).to_mongo(text_type(location))

    def to_python(self, location):
        """
        Deserialize to a UsageKey instance: for now it's a location missing the run
        """
        assert isinstance(location, (type(None), six.string_types, UsageKey))
        if location == '':
            return None
        if isinstance(location, six.string_types):
            location = super(UsageKeyField, self).to_python(location)
            return Location.from_string(location)
        else:
            return location

    def validate(self, value):
        assert isinstance(value, (type(None), six.string_types, UsageKey))
        if isinstance(value, UsageKey):
            return super(UsageKeyField, self).validate(text_type(value))
        else:
            return super(UsageKeyField, self).validate(value)

    def prepare_query_value(self, _opt, value):
        return self.to_mongo(value)
