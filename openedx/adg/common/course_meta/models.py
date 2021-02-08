"""
Models for course_meta app
"""
from django.db import models

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from .helpers import next_course_short_id


class CourseMeta(models.Model):
    """
    Model that stores meta data for a course
    """

    course = models.OneToOneField(
        CourseOverview,
        related_name='course_meta',
        on_delete=models.CASCADE,
    )
    short_id = models.PositiveSmallIntegerField(unique=True, default=next_course_short_id)

    objects = models.Manager()

    class Meta(object):
        app_label = 'course_meta'

    def __str__(self):
        return 'CourseMeta ({title}, course_id={cid}, short_id={sid})'.format(
            title=self.course.display_name, cid=self.course.id, sid=self.short_id
        )
