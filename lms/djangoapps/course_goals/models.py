"""
Goal-related models.
"""
from django.contrib.auth.models import User
from django.db import models
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class CourseGoal(models.Model):  # pylint: disable=model-missing-unicode
    """
    Represents a course goal set by a user on the course home page.
    """
    user = models.ForeignKey(User)
    course_key = CourseKeyField(max_length=255, db_index=True, blank=True)
    goal_key = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ("user", "course_key")
