import json

from django.contrib.auth.models import User
from django.db import models
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class Professor(models.Model):
    """
    professor
    """
    class Meta:
        app_label = 'professors'

    user = models.ForeignKey(
        User,
        db_index=True,
        related_name='professor_user',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=64, db_index=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    avatar = models.CharField(max_length=255, null=True, blank=True)
    info = models.TextField(max_length=10000, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_num = models.IntegerField(default=0)

    def __unicode__(self):
        return "{}-{}".format(self.name, self.description)


class ProfessorCourses(models.Model):
    """
    professor courses
    """
    class Meta:
        app_label = 'professors'

    professor = models.ForeignKey(
        Professor,
        db_index=True,
        related_name='course_professor',
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        CourseOverview,
        db_constraint=False,
        db_index=True,
        related_name='professor_courses',
        on_delete=models.CASCADE,
    )
    is_active = models.BooleanField(default=True)
    sort_num = models.IntegerField(default=0)
