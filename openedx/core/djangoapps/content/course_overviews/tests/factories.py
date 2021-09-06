

from datetime import timedelta
import json

from django.utils import timezone
import factory
from factory.django import DjangoModelFactory
from opaque_keys.edx.locator import CourseLocator

from ..models import CourseOverview


class CourseOverviewFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseOverview
        django_get_or_create = ('id', )
        exclude = ('run', )

    version = CourseOverview.VERSION
    pre_requisite_courses = []
    org = 'edX'
    run = factory.Sequence('2012_Fall_{}'.format)

    @factory.lazy_attribute
    def _pre_requisite_courses_json(self):
        return json.dumps(self.pre_requisite_courses)

    @factory.lazy_attribute
    def _location(self):
        return self.id.make_usage_key('course', 'course')

    @factory.lazy_attribute
    def id(self):
        return CourseLocator(self.org, 'toy', self.run)

    @factory.lazy_attribute
    def display_name(self):
        return "{} Course".format(self.id)

    @factory.lazy_attribute
    def start(self):
        return timezone.now()

    @factory.lazy_attribute
    def end(self):
        return timezone.now() + timedelta(30)
