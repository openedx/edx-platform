from django.db import models
from django_extensions.db.models import TimeStampedModel

from six import text_type
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from opaque_keys.edx.django.models import CourseKeyField
from xmodule.modulestore.django import modulestore
from openedx.core.lib.courses import course_image_url


class Skill(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class YearGroup(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)
    year_of_programme = models.CharField(max_length=128)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    def __str__(self):
        return self.name


class Unit(models.Model):
    course_key = CourseKeyField(db_index=True, primary_key=True, max_length=255)
    year_group = models.ForeignKey(YearGroup, null=True, on_delete=models.SET_NULL, related_name='units')

    @property
    def display_name(self):
        return CourseOverview.objects.get(id=self.course_key).display_name_with_default

    @property
    def banner_image(self):
        return CourseOverview.objects.get(id=self.course_key).banner_image_url

    @property
    def short_description(self):
        return CourseOverview.objects.get(id=self.course_key).short_description

    def __str__(self):
        return text_type(self.course_key)
