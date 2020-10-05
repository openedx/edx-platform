"""
Models for PrereqCourse app
"""
from django.db import models

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class PrereqCourse(models.Model):
    """
    Model to mark a course as prerequisite of the franchise program
    """
    course_id = CourseKeyField(db_index=True, max_length=255, null=False)
    is_enabled = models.BooleanField(default=True, null=False)

    class Meta(object):
        app_label = 'prereq_course'

    def __str__(self):
        return str(self.course_id)
