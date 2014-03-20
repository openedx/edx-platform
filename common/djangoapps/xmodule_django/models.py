from django.db import models
from xmodule.modulestore.keys import CourseKey

class CourseKeyField(models.CharField):
    description = "A CourseKey object, saved to the DB in the form of a string"

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        super(CourseKeyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, CourseKey):
            return value
        return CourseKey.from_string(value)

    def get_prep_value(self, value):
        if isinstance(value, str):
            return value
        if isinstance(value, unicode):
            return value
        return value._to_string()