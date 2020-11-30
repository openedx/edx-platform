"""
Models for course_meta app
"""
from datetime import datetime

from django.db import models

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from .helpers import next_course_short_id


class OpenPreRequisiteCourseManager(models.Manager):
    """
    Manager which returns all open pre requisite entries
    """

    def get_queryset(self):
        today = datetime.now()
        return super().get_queryset().filter(
            is_prereq=True, course__start_date__lte=today, course__end_date__gte=today
        ).prefetch_related('course').values_list('course', flat=True)


class CourseMeta(models.Model):
    """
    Model that stores meta data for a course
    """

    course = models.OneToOneField(
        CourseOverview,
        related_name='course_meta',
        on_delete=models.CASCADE,
    )
    is_prereq = models.BooleanField(default=False)
    short_id = models.PositiveSmallIntegerField(unique=True, default=next_course_short_id)

    objects = models.Manager()
    open_pre_req_courses = OpenPreRequisiteCourseManager()

    class Meta(object):
        app_label = 'course_meta'

    def __str__(self):
        return 'CourseMeta ({title}, course_id={cid}, short_id={sid})'.format(
            title=self.course.display_name, cid=self.course.id, sid=self.short_id
        )
