"""
Factories for testing program_enrollments
"""
from uuid import uuid4
import factory
from factory.fuzzy import FuzzyText
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment
from student.tests.factories import UserFactory, CourseEnrollmentFactory


class ProgramEnrollmentFactory(factory.DjangoModelFactory):
    """
    Factory for ProgramEnrollment models
    """
    class Meta(object):
        model = ProgramEnrollment

    user = factory.SubFactory(UserFactory)
    external_user_key = FuzzyText(length=16)
    program_uuid = factory.LazyFunction(uuid4)
    curriculum_uuid = factory.LazyFunction(uuid4)
    status = "enrolled"


class ProgramCourseEnrollmentFactory(factory.DjangoModelFactory):
    """
    Factory for ProgramCourseEnrollment models
    """
    class Meta(object):
        model = ProgramCourseEnrollment

    program_enrollment = factory.SubFactory(ProgramEnrollmentFactory)
    course_enrollment = factory.SubFactory(CourseEnrollmentFactory)
    course_key = CourseKey.from_string("course-v1:edX+DemoX+Demo_Course")
    status = "active"
