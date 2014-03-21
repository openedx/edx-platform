from django.db import models
from xmodule.modulestore.locations import SlashSeparatedCourseKey

class CourseKeyField(models.CharField):
    description = "A SlashSeparatedCourseKey object, saved to the DB in the form of a string"

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        super(CourseKeyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        assert isinstance(value, basestring) or isinstance(value, SlashSeparatedCourseKey)
        return CourseKey.from_string(value)

    def get_prep_value(self, value):
        assert isinstance(value, SlashSeparatedCourseKey)
        return value._to_string()