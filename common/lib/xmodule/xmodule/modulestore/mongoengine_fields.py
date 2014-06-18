"""
Custom field types for mongoengine
"""
import mongoengine
from types import NoneType
from opaque_keys.edx.keys import CourseKey, UsageKey


class CourseKeyField(mongoengine.StringField):
    """
    Serializes and deserializes CourseKey's to mongo dbs which use mongoengine
    """
    def to_mongo(self, course_key):
        """
        For now saves the course key in the deprecated form
        """
        assert isinstance(course_key, (NoneType, CourseKey))
        if course_key:
            # don't call super as base.BaseField.to_mongo calls to_python() for some odd reason
            return unicode(course_key)
        else:
            return None

    def to_python(self, course_key):
        """
        Deserialize to a CourseKey instance
        """
        # calling super b/c it decodes utf (and doesn't have circularity of from_python)
        course_key = super(CourseKeyField, self).to_python(course_key)
        assert isinstance(course_key, (NoneType, basestring, CourseKey))
        if not course_key:
            return None
        if isinstance(course_key, basestring):
            return CourseKey.from_string(course_key)
        else:
            return course_key

    def validate(self, value):
        assert isinstance(value, (NoneType, basestring, CourseKey))
        if isinstance(value, CourseKey):
            return super(CourseKeyField, self).validate(unicode(value))
        else:
            return super(CourseKeyField, self).validate(value)

    def prepare_query_value(self, _opt, value):
        return self.to_mongo(value)


class UsageKeyField(mongoengine.StringField):
    """
    Represent a UsageKey as a single string in Mongo
    """
    def to_mongo(self, usage_key):
        """
        Save the serialized usage key
        """
        assert isinstance(usage_key, (NoneType, UsageKey))
        if usage_key is None:
            return None
        return super(UsageKeyField, self).to_mongo(unicode(usage_key))

    def to_python(self, usage_key):
        """
        Deserialize to a UsageKey instance
        """
        assert isinstance(usage_key, (NoneType, basestring, UsageKey))
        if not usage_key:
            return None
        if isinstance(usage_key, basestring):
            usage_key = super(UsageKeyField, self).to_python(usage_key)
            return UsageKey.from_string(usage_key)
        else:
            return usage_key

    def validate(self, value):
        assert isinstance(value, (NoneType, basestring, UsageKey))
        if isinstance(value, UsageKey):
            return super(UsageKeyField, self).validate(unicode(value))
        else:
            return super(UsageKeyField, self).validate(value)

    def prepare_query_value(self, _opt, value):
        return self.to_mongo(value)
