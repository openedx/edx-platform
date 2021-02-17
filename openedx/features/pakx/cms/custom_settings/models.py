"""
All models for custom settings app
"""
from django.db import models
from model_utils.models import TimeStampedModel

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseOverviewContent(TimeStampedModel):
    body_html = models.TextField(blank=True, default='')
    course = models.OneToOneField(CourseOverview, related_name='custom_settings', on_delete=models.CASCADE)

    class Meta:
        app_label = 'custom_settings'

    def __str__(self):
        return 'CourseOverviewContent for course {id}'.format(id=self.course.id)
