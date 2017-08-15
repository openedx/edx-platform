import factory
from factory.django import DjangoModelFactory

from ..models import CourseOverview


class CourseOverviewFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseOverview
        django_get_or_create = ('id', )

    version = CourseOverview.VERSION

    @factory.lazy_attribute
    def _location(self):
        return self.id.make_usage_key('course', 'course')