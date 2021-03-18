"""
Factories for specializations app
"""
import factory
from factory.django import DjangoModelFactory

from openedx.features.philu_courseware.models import CourseEnrollmentMeta
from student.tests.factories import CourseEnrollmentFactory


class CourseEnrollmentMetaFactory(DjangoModelFactory):
    """
    Factory for CourseEnrollmentMeta model
    """

    class Meta(object):
        model = CourseEnrollmentMeta

    course_enrollment = factory.SubFactory(CourseEnrollmentFactory)
    program_uuid = factory.Faker('uuid4')
