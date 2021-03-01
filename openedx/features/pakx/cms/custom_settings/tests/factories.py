import factory

from openedx.features.pakx.cms.custom_settings.models import CourseOverviewContent
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


class CourseOverviewContentFactory(factory.django.DjangoModelFactory):

    class Meta(object):
        model = CourseOverviewContent

    course = factory.SubFactory(CourseOverviewFactory)
