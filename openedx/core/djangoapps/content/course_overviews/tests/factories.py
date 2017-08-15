from factory.django import DjangoModelFactory

from ..models import CourseOverview


class CourseOverviewFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseOverview
        django_get_or_create = ('id', )

    version = CourseOverview.VERSION