"""
All model factories for course_meta app
"""
import factory

from openedx.adg.common.course_meta.models import CourseMeta
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


class CourseMetaFactory(factory.DjangoModelFactory):
    class Meta:
        model = CourseMeta

    course = factory.SubFactory(CourseOverviewFactory)
