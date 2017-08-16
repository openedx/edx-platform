import json

import factory
from factory.django import DjangoModelFactory

from ..models import CourseOverview


class CourseOverviewFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseOverview
        django_get_or_create = ('id', )

    version = CourseOverview.VERSION
    pre_requisite_courses = []
    start = factory.Faker('past_datetime')

    @factory.lazy_attribute
    def _pre_requisite_courses_json(self):
        return json.dumps(self.pre_requisite_courses)

    @factory.lazy_attribute
    def _location(self):
        return self.id.make_usage_key('course', 'course')
