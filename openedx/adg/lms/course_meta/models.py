"""
Models for course_meta app
"""
from django.db import models

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class CourseMeta(models.Model):
    """
    Model that stores meta data for a course
    """
    course_id = CourseKeyField(max_length=255, unique=True)
    is_prereq = models.BooleanField(default=False)

    class Meta(object):
        app_label = 'course_meta'

    def __str__(self):
        return str(self.course_id)
