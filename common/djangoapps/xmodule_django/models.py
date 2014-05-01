from django.db import models
from xmodule.modulestore.locations import SlashSeparatedCourseKey, Location
from types import NoneType


class CourseKeyField(models.CharField):
    description = "A SlashSeparatedCourseKey object, saved to the DB in the form of a string"

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        super(CourseKeyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        assert isinstance(value, (NoneType, basestring, SlashSeparatedCourseKey))
        if not value:
            # handle empty string for models being created w/o fields populated
            return None
        if isinstance(value, basestring):
            return SlashSeparatedCourseKey.from_deprecated_string(value)
        else:
            return value

    def get_prep_value(self, value):
        assert isinstance(value, (NoneType, SlashSeparatedCourseKey))
        return value.to_deprecated_string() if value else None

    def validate(self, value, model_instance):
        # The default django CharField validator tries to call len() on SlashSeparatedCourseKey,
        # so we write custom validation that allows us to use SlashSeparatedCourseKeys
        assert isinstance(value, (NoneType, basestring, SlashSeparatedCourseKey))

    def run_validators(self, value):
        # The default django CharField validator tries to call len() on SlashSeparatedCourseKey,
        # so we write custom validation that allows us to use SlashSeparatedCourseKeys
        if isinstance(value, SlashSeparatedCourseKey):
            assert len(value.to_deprecated_string()) <= self.max_length


class LocationKeyField(models.CharField):
    description = "A Location object, saved to the DB in the form of a string"

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        super(LocationKeyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        assert isinstance(value, (NoneType, basestring, Location))
        if not value:
            return None
        if isinstance(value, basestring):
            return Location.from_deprecated_string(value)
        else:
            return value

    def get_prep_value(self, value):
        assert isinstance(value, Location)
        return value.to_deprecated_string() if value else ''

    def validate(self, value, model_instance):
        # The default django CharField validator tries to call len() on Locations,
        # so we write custom validation that allows us to use Locations
        assert isinstance(value, (NoneType, basestring, Location))

    def run_validators(self, value):
        # The default django CharField validator tries to call len() on Locations,
        # so we write custom validation that allows us to use Locations
        if isinstance(value, Location):
            assert len(value.to_deprecated_string()) <= self.max_length
